"""
DevPulseAI v3 — FastAPI Backend + WebSocket Chat

Endpoints:
  WebSocket  /ws/chat             — Real-time streaming chat
  POST       /api/chat             — REST fallback for chat
  POST       /api/feedback         — Submit 👍/👎 → Supabase
  GET        /api/signals          — Query raw_signals for dashboard
  GET        /api/intelligence     — Query processed_intelligence
  GET        /api/conversations    — Fetch chat history
  GET        /api/recommendations  — Proactive suggestions
  GET        /ping                 — Health check (Render cron)
  POST       /ingest               — Signal ingestion (v2 compat)
  POST       /daily-pulse          — Full ingestion cycle (v2 compat)
"""

import asyncio
import json
import uuid
import traceback

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List

from app.core.conversation import ConversationManager
from app.persistence.client import db
from app.core.logger import logger

# ── App Setup ──────────────────────────────────────────

app = FastAPI(
    title="DevPulseAI v3 API",
    version="3.0.0",
    description="Autonomous Technical Intelligence — Chat, Signals, Knowledge"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request/Response Models ────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    intent: Optional[str] = None

class FeedbackRequest(BaseModel):
    conversation_id: str
    vote_type: str  # "positive" or "negative"
    message_preview: Optional[str] = None

class IngestRequest(BaseModel):
    source: str
    run_agents: bool = True

# ── Conversation Manager Pool ──────────────────────────
# Cache managers by conversation_id for session continuity

_managers = {}

def get_manager(conversation_id: str = None) -> ConversationManager:
    """Get or create a ConversationManager for a session."""
    if conversation_id and conversation_id in _managers:
        return _managers[conversation_id]
    
    mgr = ConversationManager()
    if conversation_id:
        mgr.conversation_id = conversation_id
    _managers[mgr.conversation_id] = mgr
    
    # Cap pool size
    if len(_managers) > 50:
        oldest_key = next(iter(_managers))
        del _managers[oldest_key]
    
    return mgr


# ── Health ─────────────────────────────────────────────

@app.get("/ping")
async def ping():
    """Ultra-lightweight health check for Render cron wake-up."""
    return {"status": "ok", "version": "3.0.0"}


@app.get("/")
async def root():
    return {"message": "DevPulseAI v3 API", "docs": "/docs"}


# ── Chat Endpoints ─────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    REST chat endpoint. Sends message to ConversationManager,
    returns full response.
    """
    try:
        mgr = get_manager(req.conversation_id)
        response = await mgr.process_message(req.message)
        return ChatResponse(
            response=response,
            conversation_id=mgr.conversation_id,
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming chat.
    
    Client sends: {"message": "...", "conversation_id": "..."}
    Server sends: {"type": "response", "content": "...", "conversation_id": "..."}
    """
    await websocket.accept()
    mgr = None
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            message = payload.get("message", "")
            conv_id = payload.get("conversation_id")
            
            if not message:
                await websocket.send_json({"type": "error", "content": "Empty message"})
                continue
            
            if mgr is None or (conv_id and conv_id != mgr.conversation_id):
                mgr = get_manager(conv_id)
            
            # Send "typing" indicator
            await websocket.send_json({
                "type": "typing",
                "conversation_id": mgr.conversation_id
            })
            
            # Process message
            try:
                response = await mgr.process_message(message)
                await websocket.send_json({
                    "type": "response",
                    "content": response,
                    "conversation_id": mgr.conversation_id
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Processing error: {str(e)}",
                    "conversation_id": mgr.conversation_id
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


# ── Feedback ───────────────────────────────────────────

@app.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Submit user feedback (👍/👎) → Supabase user_feedback table."""
    try:
        db.save_feedback(
            signal_id=req.conversation_id,
            vote_type=req.vote_type,
            feedback_text=req.message_preview,
        )
        return {"status": "saved", "vote_type": req.vote_type}
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Data Queries ───────────────────────────────────────

@app.get("/api/signals")
async def get_signals(source: Optional[str] = None, limit: int = Query(20, le=100)):
    """Query raw signals with optional source filter."""
    try:
        return db.query_signals(source=source, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/intelligence")
async def get_intelligence(agent_name: Optional[str] = None, limit: int = Query(20, le=100)):
    """Query processed intelligence with optional agent filter."""
    try:
        return db.query_intelligence(agent_name=agent_name, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{conversation_id}")
async def get_conversations(conversation_id: str, limit: int = Query(50, le=200)):
    """Fetch chat history for a conversation."""
    try:
        return db.get_conversations(conversation_id, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Recommendations ───────────────────────────────────

@app.get("/api/recommendations")
async def get_recommendations(conversation_id: Optional[str] = None, limit: int = 5):
    """Get proactive recommendations based on recent activity."""
    try:
        from app.core.recommendations import RecommendationEngine
        engine = RecommendationEngine()
        recs = await engine.get_recommendations(
            conversation_id=conversation_id,
            limit=limit
        )
        return recs
    except ImportError:
        return []
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        return []


# ── Ingestion (v2 compat) ─────────────────────────────

@app.post("/ingest")
async def trigger_ingestion(req: IngestRequest, background_tasks: BackgroundTasks):
    """Trigger signal ingestion from a source (v2 compatible)."""
    background_tasks.add_task(_run_ingestion, req.source, req.run_agents)
    return {"status": "accepted", "message": f"Ingestion started for {req.source}"}


@app.post("/daily-pulse")
async def trigger_daily_pulse(background_tasks: BackgroundTasks):
    """Trigger full ingestion cycle across all sources."""
    async def _run_cycle():
        sources = ["github", "huggingface", "arxiv", "hackernews"]
        for source in sources:
            try:
                await _run_ingestion(source, run_agents=True)
            except Exception as e:
                logger.error(f"Ingestion failed for {source}: {e}")

    background_tasks.add_task(_run_cycle)
    return {"status": "started", "message": "Daily Pulse triggered"}


async def _run_ingestion(source: str, run_agents: bool = True):
    """Run ingestion from a specific source, store to Supabase + Pinecone."""
    from app.adapters.github import GitHubAdapter
    from app.adapters.huggingface import HuggingFaceAdapter
    from app.adapters.arxiv import ArXivAdapter
    from app.adapters.hackernews import HackerNewsAdapter

    logger.info(f"Starting ingestion for {source}")
    signals = []

    if source == "github":
        signals = await GitHubAdapter().fetch_trending()
    elif source == "huggingface":
        hf = HuggingFaceAdapter()
        signals = await hf.fetch_new_models()
        # Also fetch papers and spaces for richer signal coverage
        signals.extend(await hf.fetch_papers())
        signals.extend(await hf.fetch_trending_spaces())
    elif source == "arxiv":
        signals = await ArXivAdapter().fetch_recent_papers()
    elif source == "hackernews":
        signals = await HackerNewsAdapter().fetch_stories()
    else:
        logger.error(f"Unknown source: {source}")
        return

    # Store & deduplicate
    new_count = 0
    for sig in signals:
        try:
            record = db.insert_raw_signal(
                sig.source, sig.external_id,
                sig.model_dump(mode='json'),
                sig.generate_hash()
            )
            if record:
                new_count += 1
                # Also store in Pinecone for semantic search
                _store_signal_in_pinecone(record['id'], sig)
        except Exception as e:
            logger.error(f"Insert signal {sig.external_id}: {e}")

    logger.info(f"Ingested {new_count} new signals from {source}")


def _store_signal_in_pinecone(signal_id: str, sig):
    """Store an ingested signal in Pinecone for semantic search."""
    try:
        from pinecone import Pinecone
        import os
        pc_key = os.environ.get("PINECONE_API_KEY")
        if not pc_key:
            return
        pc = Pinecone(api_key=pc_key)
        idx = pc.Index("devpulseai-knowledge")
        idx.upsert_records(
            namespace="signals",
            records=[{
                "_id": signal_id,
                "content": f"{sig.title}\n{sig.content[:500]}",
                "source": sig.source,
                "signal_type": "ingested",
            }]
        )
    except Exception as e:
        logger.warning(f"Pinecone store warning: {e}")
