
# DevPulseAI v3 — Autonomous Signal Intelligence Platform

> **Ingest. Analyze. Deliver.**
> Real-time technical intelligence powered by multi-agent AI, cost-aware model routing, and Model Context Protocol (MCP).

---

## ⚡ Overview

**DevPulseAI v3** is a cloud-native intelligence platform that autonomously aggregates signals from high-value developer sources, processes them through a multi-agent LLM pipeline, and delivers curated, actionable intelligence — via real-time chat, REST API, proactive alerts, or scheduled digest.

v3 introduces:

- **MCP-first architecture** — 4 MCP servers (GitHub, HuggingFace, Supabase, Pinecone) replace brittle REST scrapers
- **Codebase-Aware Intelligence** — signals scored against your actual dependency graph
- **Vector Knowledge Graph** — entities extracted and linked across repos, papers, and libraries
- **Ephemeral Worker Agents** — CommunityVibe, RiskAnalyst, DependencyImpact — spawned per-task
- **Cost-Aware Model Routing** — tiered LLM selection (fast/mid/strong) with cost tracking
- **Proactive Alerts** — Discord, Slack, and email webhooks for CVEs and breaking changes

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
│  └──────────┘  └──────────────┘  └──────────┘  └─────────────┘  │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                INGESTION PIPELINE (server.py)                     │
│                                                                  │
│  Ingest → Deduplicate → Relevance Score → Pinecone Index         │
│                          → KG Entity Extract → Alert Dispatch    │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│           MULTI-SWARM AGENT PIPELINE (7 workers)                 │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐         │
│  │ Researcher  │  │   Analyst   │  │ ProjectExplorer  │         │
│  │(Repo Search)│  │(Paper/Data) │  │ (Local Context)  │         │
│  └─────────────┘  └─────────────┘  └──────────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐         │
│  │ Community   │  │    Risk     │  │   Dependency     │         │
│  │ VibeAgent   │  │   Analyst   │  │ ImpactAnalyzer   │         │
│  └─────────────┘  └─────────────┘  └──────────────────┘         │
│                                                                  │
│  Cost-Aware Router: fast(gpt-4.1-mini) → strong(gpt-4.1)        │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                     DELIVERY LAYER                                │
│                                                                  │
│  WebSocket Chat · REST API · Streamlit Dashboard                  │
│  Discord/Slack Alerts · Email Digest · 17 API Endpoints           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🧠 v3 Intelligence Features

### Codebase-Aware Intelligence (SOW §5)

Parses your project's `requirements.txt`, `package.json`, and `pyproject.toml` to build a dependency graph. Every ingested signal is scored against your stack — CVEs in packages you use get boosted to the top.

```python
# Scan your project
POST /api/context {"project_path": "/path/to/project"}

# Signals now carry codebase_relevance scores (0.0 - 1.0)
```

### Vector Knowledge Graph (SOW §4.1)

Regex-based entity extraction identifies 5 entity types from every signal:

| Entity Type | Example | Detection |
|---|---|---|
| **Repository** | `huggingface/transformers` | GitHub URL regex |
| **Paper** | `arxiv:2401.12345` | ArXiv ID / DOI patterns |
| **Library** | `pytorch`, `fastapi` | Known library names |
| **Concept** | `RAG`, `LoRA`, `Fine-Tuning` | AI/ML keyword map |
| **Author** | — | Placeholder (future) |

Entities → **Pinecone** (semantic search), Edges → **Supabase** (`knowledge_edges` table).

### Ephemeral Worker Agents (SOW §3)

| Worker | Trigger Keywords | What It Does |
|---|---|---|
| `CommunityVibeAgent` | "community vibe", "sentiment", "hype" | Lexicon-based sentiment analysis from HN + internal signals |
| `RiskAnalyst` | "risk", "cve", "security", "vulnerability" | CVE/breaking change scanner with ProjectContext cross-reference |
| `DependencyImpactAnalyzer` | "dependency impact", "impact of updating" | Traces update impact through dependency chain |

### Cost-Aware Model Routing (SOW §7)

| Tier | Model | Use Case | Cost/M Tokens |
|---|---|---|---|
| **fast** | `gpt-4.1-mini` | Intent classification, cleanup | $0.40 |
| **mid** | `gpt-4.1-mini` | Worker reasoning (default) | $0.40 |
| **strong** | `gpt-4.1` | Final synthesis, complex analysis | $2.00 |

Override via env vars: `MODEL_FAST`, `MODEL_MID`, `MODEL_STRONG`

### Proactive Alerts (SOW §6.2)

Automatically dispatched during ingestion when critical signals are detected:

- 🚨 **CVE_DETECTED** → `CRITICAL` severity
- 🔴 **BREAKING_CHANGE** → `HIGH` severity

Channels: **Discord** (webhook embeds), **Slack** (Block Kit), **Email** (Resend)

---

## 🔌 MCP Server Integration

| Server | Purpose | Key Tools |
|---|---|---|
| **GitHub MCP** | Trending repos, code search, deep-dive analysis | `search_repositories`, `get_file_contents` |
| **HuggingFace MCP** | Models, papers, datasets, Spaces discovery | `hub_repo_search`, `paper_search` |
| **Supabase MCP** | Persistent storage (8 tables + RLS policies) | `execute_sql`, `apply_migration` |
| **Pinecone MCP** | Semantic vector search + knowledge embeddings | `search-records`, `upsert-records` |

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

## 🚀 FastAPI Backend — 17 Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/ws/chat` | WebSocket | Real-time streaming chat with MultiSwarm agents |
| `/api/chat` | POST | REST fallback for chat (non-streaming) |
| `/api/feedback` | POST | Submit 👍/👎 feedback → Supabase |
| `/api/signals` | GET | Query raw signals from Supabase |
| `/api/intelligence` | GET | Query processed intelligence |
| `/api/conversations/{id}` | GET | Retrieve conversation history |
| `/api/recommendations` | GET | Pinecone-powered proactive recommendations |
| `/api/context` | POST | Scan project dependencies → build context graph |
| `/api/model-router/status` | GET | Model routing config + accumulated cost |
| `/api/alerts/status` | GET | Alert system config + recent dispatch history |
| `/ingest` | POST | Trigger signal ingestion from a specific source |
| `/daily-pulse` | POST | Run full pipeline: ingest → process → store → alert |
| `/ping` | GET | Health check for Render keep-alive |
| `/openapi.json` | GET | OpenAPI spec |
| `/docs` | GET | Swagger UI |
| `/redoc` | GET | ReDoc UI |
| `/` | GET | Static frontend |

---

## 📋 v3 Phase Tracker

### ✅ Completed

| Phase | Features |
|---|---|
| **Phase 1 — Foundation** | Streamlit UI, MultiSwarm agents, Conversation pipeline, Signal/Intelligence models |
| **Phase 2 — MCP Integration** | Supabase (8 tables), GitHub MCP, Pinecone MCP, ArXiv fixes, Persistence client |
| **Phase 3 — Backend** | FastAPI (17 endpoints), WebSocket chat, HuggingFace adapter, Recommendation engine |
| **Phase 4 — Intelligence** | Codebase-Aware scoring, Vector Knowledge Graph, Ephemeral workers, Model routing, Proactive alerts |

### 🔲 Upcoming

| Phase | Features | Priority |
|---|---|---|
| **Phase 5 — Deployment** | Render deployment, cron-job `/daily-pulse`, production monitoring | 🔴 High |
| **Phase 5 — Frontend** | React/Next.js UI, WebSocket chat, Signal feed dashboard | 🔴 High |
| **Phase 6 — Polish** | User auth + sessions, email digest, trend detection | 🟡 Medium |

---

## 🛠 Local Development

```bash
# Clone
git clone https://github.com/STiFLeR7/DevPulseAIv2.git
cd DevPulseAIv2
git checkout feat/v3

# Install
pip install -r requirements.txt

# Configure (.env)
GEMINI_API_KEY=...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
PINECONE_API_KEY=pcsk_...

# Optional
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...
HUGGINGFACE_TOKEN=hf_...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Run FastAPI backend
uvicorn app.api.server:app --reload --port 8000

# Or Streamlit UI
streamlit run app/ui/chat.py

# Run tests
python -m scripts.test_codebase_context
python -m scripts.test_knowledge_graph
python -m scripts.test_workers
```

---

## 📂 Project Structure

```
DevPulseAIv2/
├── app/
│   ├── adapters/              # Signal source adapters
│   │   ├── github.py          # GitHub trending repos
│   │   ├── arxiv.py           # ArXiv AI/ML papers
│   │   ├── hackernews.py      # HackerNews top stories
│   │   ├── medium.py          # Medium RSS blogs
│   │   └── huggingface.py     # HuggingFace models/papers/spaces
│   ├── agents/                # LLM agent workers
│   │   ├── researcher.py      # RepoResearcher (GitHub deep-dive)
│   │   ├── analyst.py         # PaperAnalyst (research papers)
│   │   ├── explorer.py        # ProjectExplorer (local context)
│   │   ├── community_vibe.py  # CommunityVibeAgent (sentiment) ★
│   │   ├── risk_analyst.py    # RiskAnalyst (CVE/risk scan) ★
│   │   └── dependency_impact.py # DependencyImpactAnalyzer ★
│   ├── api/
│   │   ├── server.py          # v3 FastAPI + WebSocket (17 endpoints)
│   │   └── main.py            # v2 legacy
│   ├── core/
│   │   ├── swarm.py           # MultiSwarm orchestration engine
│   │   ├── conversation.py    # Conversation pipeline + intent routing
│   │   ├── codebase_context.py # Dependency parser + relevance scorer ★
│   │   ├── model_router.py    # Cost-aware tiered model selection ★
│   │   ├── alerts.py          # Proactive alert dispatcher ★
│   │   ├── recommendations.py # Pinecone + Supabase recommendations
│   │   └── logger.py          # Structured logging
│   ├── memory/
│   │   ├── graph.py           # Vector Knowledge Graph ★
│   │   └── vector_store.py    # Pinecone vector ops
│   ├── models/                # Pydantic data models
│   ├── persistence/           # Supabase client + schema
│   ├── reports/               # HTML email generation
│   └── ui/
│       └── chat.py            # Premium Streamlit chat interface
├── scripts/
│   ├── test_codebase_context.py    # Tests: dep parsing + scoring
│   ├── test_knowledge_graph.py     # Tests: entity extraction + KG
│   ├── test_workers.py             # Tests: workers + router + alerts
│   ├── migrate_project_context.py  # Supabase migration
│   └── migrate_knowledge_edges.py  # Supabase migration
├── Dockerfile
├── requirements.txt
└── README.md
```

> ★ = New in v3

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | Gemini LLM for agent pipeline |
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase service role key |
| `PINECONE_API_KEY` | ✅ | Pinecone vector search |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | Optional | Higher rate limits for GitHub API |
| `HUGGINGFACE_TOKEN` | Optional | Higher rate limits for HuggingFace API |
| `DISCORD_WEBHOOK_URL` | Optional | Discord alert channel |
| `SLACK_WEBHOOK_URL` | Optional | Slack alert channel |
| `ALERT_EMAIL` | Optional | Email alerts (via Resend) |
| `MODEL_FAST` | Optional | Override fast-tier model (default: `gpt-4.1-mini`) |
| `MODEL_MID` | Optional | Override mid-tier model (default: `gpt-4.1-mini`) |
| `MODEL_STRONG` | Optional | Override strong-tier model (default: `gpt-4.1`) |

---

> **Built with ❤️ by Hill Patel.**
> *Powered by Gemini · Supabase · Pinecone · MCP*
