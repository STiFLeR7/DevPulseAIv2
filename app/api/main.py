from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from app.adapters.github import GitHubAdapter
from app.adapters.huggingface import HuggingFaceAdapter
from app.adapters.medium import MediumAdapter
from app.adapters.arxiv import ArXivAdapter
from app.adapters.twitter import TwitterAdapter
from app.persistence.client import db
from app.inference.gemini_client import GeminiClient
from app.agents.implementations import SummarizationAgent, RelevanceAgent, RiskAgent
from app.agents.trend import TrendDetectionAgent
from app.models.signal import Signal
from app.core.logger import logger
from app.core.mailer import MailerService
import asyncio

app = FastAPI(title="DevPulseAI v2 API", version="0.1.0")

# CORS (Allow all for Dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency Injection
inference_client = GeminiClient()
agents = {
    "summary": SummarizationAgent(inference_client),
    "relevance": RelevanceAgent(inference_client),
    "risk": RiskAgent(inference_client)
}
trend_agent = TrendDetectionAgent(inference_client)
mailer = MailerService()

# Serve UI
app.mount("/dashboard", StaticFiles(directory="app/static", html=True), name="static")

@app.get("/")
async def read_root():
    return FileResponse('app/static/index.html')

@app.get("/ping")
async def ping():
    """Ultra-lightweight health check for cron wake-up."""
    return {"status": "ok"}

class TriggerRequest(BaseModel):
    source: str
    run_agents: bool = True

@app.post("/ingest")
async def trigger_ingestion(req: TriggerRequest, background_tasks: BackgroundTasks):
    """
    Webhook to trigger ingestion from a specific source.
    """
    background_tasks.add_task(run_ingestion_task, req.source, req.run_agents)
    return {"status": "accepted", "message": f"Ingestion started for {req.source}"}

@app.post("/daily-pulse")
async def trigger_full_cycle(background_tasks: BackgroundTasks):
    """
    Triggers the FULL Daily Cycle:
    1. Ingest from all sources.
    2. Run Agents.
    3. Generate & Send Email Report.
    """
    async def _run_cycle():
        sources = ["github", "huggingface", "medium", "arxiv", "twitter"]
        for source in sources:
            try:
                await run_ingestion_task(source, run_agents=True)
            except Exception as e:
                logger.error(f"Ingestion failed for {source}: {e}")
        
        # After ingestion complete, generate report
        from app.reports.daily import DailyReportGenerator
        generator = DailyReportGenerator()
        try:
            html = generator.generate_html_report()
            mailer.send_daily_report(html)
        except Exception as e:
            logger.error(f"Report generation/sending failed: {e}")

    background_tasks.add_task(_run_cycle)
    return {"status": "started", "message": "Daily Pulse triggered (Ingest -> Process -> Email)"}

@app.post("/report")
async def trigger_report(background_tasks: BackgroundTasks):
    """
    Generates the daily report AND sends it via email.
    """
    from app.reports.daily import DailyReportGenerator
    generator = DailyReportGenerator()
    
    try:
        html_content = generator.generate_html_report()
        
        # Send Email in background to not block UI
        background_tasks.add_task(mailer.send_daily_report, html_content)
        
        return {"status": "generated", "message": "Report generated and email queued."}
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/intelligence")
async def get_intelligence(limit: int = 50):
    """
    Fetches recent processed intelligence for the UI dashboard.
    """
    try:
        # Join logic (Application side for simplicity without View)
        # 1. Fetch Intelligence
        intel_res = db.get_client().table("processed_intelligence").select("*").order("created_at", desc=True).limit(limit).execute()
        intel_data = intel_res.data if intel_res.data else []
        
        # 2. Fetch related Signals
        if not intel_data:
            return []
            
        signal_ids = list(set([x['signal_id'] for x in intel_data]))
        signals_res = db.get_client().table("raw_signals").select("*").in_("id", signal_ids).execute()
        signals_map = {x['id']: x for x in signals_res.data} if signals_res.data else {}
        
        # 3. Combine
        feeds = []
        for i in intel_data:
            sig = signals_map.get(i['signal_id'])
            if not sig: continue
            
            feeds.append({
                "id": i['id'],
                "title": sig['payload'].get('title', 'Unknown'),
                "url": sig['payload'].get('url', '#'),
                "source": sig['source'],
                "agent": i['agent_name'],
                "model": i['agent_version'],
                "output": i['output_data'],
                "timestamp": i['created_at']
            })
            
        return feeds
    except Exception as e:
        logger.error(f"Fetch intelligence failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_ingestion_task(source: str, run_agents: bool):
    logger.info(f"Starting ingestion for {source}")
    signals = []
    
    # 1. Fetch
    if source == "github":
        adapter = GitHubAdapter()
        signals = await adapter.fetch_trending()
    elif source == "huggingface":
        adapter = HuggingFaceAdapter()
        signals = await adapter.fetch_new_models()
    elif source == "medium":
        adapter = MediumAdapter()
        signals = await adapter.fetch_feed_updates()
    elif source == "arxiv":
        adapter = ArXivAdapter()
        signals = await adapter.fetch_recent_papers()
    elif source == "twitter":
        adapter = TwitterAdapter()
        signals = await adapter.fetch_tweets()
    else:
        logger.error(f"Unknown source: {source}")
        return

    # 2. Store & Deduplicate
    new_signals_map = {} # Map signal object to DB ID
    
    for sig in signals:
        try:
            record = db.insert_raw_signal(sig.source, sig.external_id, sig.model_dump(mode='json'), sig.generate_hash())
            if record:
                new_signals_map[record['id']] = sig
        except Exception as e:
            logger.error(f"Failed to insert signal {sig.external_id}: {e}")

    logger.info(f"Ingested {len(new_signals_map)} new signals from {source}")

    # 3. Agent Processing
    if run_agents and new_signals_map:
        await process_signals(new_signals_map)

async def process_signals(signals_map: dict):
    # signals_map is {db_id: SignalObject}
    for db_id, sig in signals_map.items():
        # Summary
        try:
            res_sum = await agents["summary"].process(sig)
            db.insert_intelligence(db_id, "summarization", agents["summary"].model_id, res_sum)
            
            # Relevance
            res_rel = await agents["relevance"].process(sig)
            db.insert_intelligence(db_id, "relevance", agents["relevance"].model_id, res_rel)
            
            # Risk
            res_risk = await agents["risk"].process(sig)
            db.insert_intelligence(db_id, "risk_analysis", agents["risk"].model_id, res_risk)
        except Exception as e:
            logger.error(f"Failed processing agents for {sig.external_id}: {e}")

    # Batch Process: Trend Detection
    try:
        if len(signals_map) > 0:
            logger.info("Running Trend Detection on batch...")
            # Convert map values to list
            signal_list = list(signals_map.values())
            trends = await trend_agent.analyze_batch(signal_list)
            
            # Store Trends
            anchor_id = list(signals_map.keys())[0]
            
            for trend in trends:
                db.insert_intelligence(anchor_id, "trend_detection", trend_agent.model_id, trend)
    except Exception as e:
        logger.error(f"Trend Detection Failed: {e}")
