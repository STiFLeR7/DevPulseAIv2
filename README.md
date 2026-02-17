
# DevPulseAI v3 — Autonomous Signal Intelligence Platform

> **Ingest. Analyze. Deliver.**
> Real-time technical intelligence powered by multi-agent AI and Model Context Protocol (MCP).

---

## ⚡ Overview

**DevPulseAI v3** is a cloud-native intelligence platform that autonomously aggregates signals from high-value developer sources, processes them through a multi-agent LLM pipeline, and delivers curated, actionable intelligence — via a real-time chat interface, REST API, or scheduled digest.

v3 introduces **MCP-first architecture**: four MCP servers (GitHub, HuggingFace, Supabase, Pinecone) provide structured, authenticated access to external services — replacing brittle REST scrapers with reliable, tool-backed integrations.

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       SIGNAL SOURCES                             │
│  GitHub · ArXiv · HackerNews · Medium · HuggingFace              │
│   (5 adapters, ~25 signals per cycle)                            │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│               MCP LAYER (Model Context Protocol)                 │
│                                                                  │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌─────────────┐  │
│  │ GitHub   │  │ HuggingFace  │  │ Supabase │  │  Pinecone   │  │
│  │ MCP      │  │ MCP          │  │ MCP      │  │  MCP        │  │
│  │ Server   │  │ Server       │  │ Server   │  │  Server     │  │
│  └──────────┘  └──────────────┘  └──────────┘  └─────────────┘  │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    AGENT PIPELINE                                 │
│                                                                  │
│  Ingestion → Normalization → MultiSwarm Processing               │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐         │
│  │ Researcher  │  │  Analyst    │  │     Critic       │         │
│  │ (Summarize) │  │ (Score+Risk)│  │ (Verify+Refine)  │         │
│  └─────────────┘  └─────────────┘  └──────────────────┘         │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                     DELIVERY LAYER                                │
│                                                                  │
│  WebSocket Chat · REST API · Streamlit Dashboard · Email Digest   │
│  FastAPI (10 endpoints) · Proactive Recommendations               │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔌 MCP Server Integration

DevPulseAI v3 uses **four MCP servers** as the backbone for external data access. Each serves a distinct purpose in the pipeline:

### GitHub MCP Server

| | |
|---|---|
| **Purpose** | Fetch trending repositories, search code, read file contents, manage issues/PRs |
| **Use in Pipeline** | The GitHub adapter queries trending repos created in the last 24 hours, extracts star counts, languages, and topics as signals. Also supports deep-dive repo analysis when users ask about specific repositories in the chat interface. |
| **Key Tools Used** | `search_repositories`, `get_file_contents`, `search_code` |
| **Auth** | `GITHUB_PERSONAL_ACCESS_TOKEN` |

### HuggingFace MCP Server

| | |
|---|---|
| **Purpose** | Search models, papers, datasets, and Spaces from the HuggingFace Hub |
| **Use in Pipeline** | Three signal streams: **(1)** Trending models with download counts, task types, and trending scores. **(2)** Daily research papers with author info and upvotes. **(3)** Popular Spaces with SDK info. Falls back to REST API if MCP is unavailable. |
| **Key Tools Used** | `hub_repo_search`, `paper_search`, `space_search` |
| **Auth** | `HUGGINGFACE_TOKEN` (optional, increases rate limits) |

### Supabase MCP Server

| | |
|---|---|
| **Purpose** | Persistent storage for all pipeline data — signals, intelligence, conversations, feedback |
| **Use in Pipeline** | Every signal flows through Supabase: raw signals are stored on ingestion, processed intelligence after agent analysis, conversation history for the chat interface, user feedback (👍/👎) for quality tracking, and audit logs for observability. |
| **Tables** | `raw_signals` (347+), `processed_intelligence` (1028+), `conversations` (18+), `audit_logs` (7+), `agent_traces` (45+), `user_feedback` |
| **Auth** | `SUPABASE_ACCESS_TOKEN` |

### Pinecone MCP Server

| | |
|---|---|
| **Purpose** | Semantic vector search for intelligent recommendations and knowledge retrieval |
| **Use in Pipeline** | Stores processed intelligence as embeddings in the `devpulseai-knowledge` index (multilingual-e5-large). Powers the `/api/recommendations` endpoint — finds semantically similar signals to user queries. Enables the proactive recommendation engine that suggests relevant repos, papers, and topics based on conversation history. |
| **Key Tools Used** | `search-records`, `upsert-records`, `describe-index` |
| **Auth** | `PINECONE_API_KEY` |

---

## 📡 Signal Sources & Adapters

| Source | Adapter | Data Fetched | Signals/Cycle |
|---|---|---|---|
| **GitHub** | `adapters/github.py` | Trending repos (24h), stars, languages, topics | ~5-10 |
| **ArXiv** | `adapters/arxiv.py` | Latest AI/ML papers, abstracts, authors | ~5-10 |
| **HackerNews** | `adapters/hackernews.py` | Top stories, points, comment counts | ~5-10 |
| **Medium** | `adapters/medium.py` | AI/ML engineering blogs (RSS feeds) | ~3-5 |
| **HuggingFace** | `adapters/huggingface.py` | Trending models, daily papers, popular Spaces | ~9-15 |

---

## 🚀 FastAPI Backend — 10 Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/ws/chat` | WebSocket | Real-time streaming chat with MultiSwarm agents |
| `/api/chat` | POST | REST fallback for chat (non-streaming) |
| `/api/feedback` | POST | Submit 👍/👎 feedback → Supabase `user_feedback` |
| `/api/signals` | GET | Query raw signals from Supabase |
| `/api/intelligence` | GET | Query processed intelligence |
| `/api/conversations` | GET | Retrieve conversation history |
| `/api/recommendations` | GET | Pinecone-powered proactive recommendations |
| `/ingest` | POST | Trigger signal ingestion from a specific source |
| `/daily-pulse` | POST | Run full pipeline: ingest all → process → store |
| `/ping` | GET | Health check for Render keep-alive |

---

## 📋 v3 Phase Tracker

### ✅ Completed

| Phase | Features | Commit |
|---|---|---|
| **Phase 1 — Foundation** | Premium Streamlit UI (glassmorphism, dark theme), MultiSwarm agent system (Researcher, Analyst, Critic), Conversation pipeline, Signal/Intelligence models, Custom logger | `7e99c63` |
| **Phase 2 — MCP Integration** | Supabase MCP (6 tables + RLS policies), GitHub MCP (real API), Pinecone MCP (`devpulseai-knowledge` index, 4 records seeded), ArXiv fix (stopword stripping), Persistence client (datetime + conversation methods), End-to-end data flow verified | `d4d8d7b` |
| **Phase 3 — Backend + Features** | FastAPI `server.py` (10 endpoints), WebSocket chat, REST chat, Feedback → Supabase, Proactive recommendation engine (Pinecone + Supabase), HuggingFace MCP adapter (models + papers + spaces), HackerNews adapter, Ingestion pipeline | `48b6f5a` |

### 🔲 Upcoming

| Phase | Features | Priority |
|---|---|---|
| **Phase 4 — Deployment** | Render deployment (Procfile, env config), Cron-job for `/daily-pulse`, Production health monitoring | 🔴 High |
| **Phase 4 — Frontend** | React/Next.js UI connecting to FastAPI, WebSocket chat integration, Signal feed dashboard | 🔴 High |
| **Phase 5 — Intelligence** | Pinecone auto-storage from conversations, Scheduled ingestion pipeline, Trend detection over time | 🟡 Medium |
| **Phase 5 — Polish** | User authentication + sessions, Multi-provider LLM fallback chains, Email digest generation | 🟠 Low |

---

## 🛠 Local Development

```bash
# Clone the repo
git clone https://github.com/STiFLeR7/DevPulseAIv2.git
cd DevPulseAIv2
git checkout feat/v3

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=sk-...
export SUPABASE_URL=https://xxx.supabase.co
export SUPABASE_KEY=eyJ...
export PINECONE_API_KEY=pcsk_...

# Run FastAPI backend
uvicorn app.api.server:app --reload --port 8000

# Or run Streamlit UI
streamlit run app/ui/chat.py
```

---

## 📂 Project Structure

```
DevPulseAIv2/
├── app/
│   ├── adapters/          # Signal source adapters (GitHub, ArXiv, HF, HN, Medium)
│   ├── agents/            # LLM agents (Researcher, Analyst, Critic)
│   ├── api/
│   │   ├── main.py        # v2 FastAPI (legacy)
│   │   └── server.py      # v3 FastAPI + WebSocket (10 endpoints)
│   ├── core/
│   │   ├── swarm.py       # MultiSwarm orchestration
│   │   ├── conversation.py # Conversation pipeline
│   │   ├── recommendations.py # Pinecone + Supabase recommendation engine
│   │   └── logger.py      # Structured logging
│   ├── models/            # Pydantic models (Signal, Intelligence)
│   ├── persistence/       # Supabase client + schema
│   ├── reports/           # HTML email generation
│   └── ui/
│       └── chat.py        # Premium Streamlit chat interface
├── scripts/               # Test & verification scripts
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | LLM provider for agent pipeline |
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase service role key |
| `PINECONE_API_KEY` | ✅ | Pinecone vector search |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | Optional | Higher rate limits for GitHub API |
| `HUGGINGFACE_TOKEN` | Optional | Higher rate limits for HuggingFace API |

---

> **Built with ❤️ by Hill Patel.**
> *Powered by OpenAI · Supabase · Pinecone · MCP*
