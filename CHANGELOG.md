# Changelog

All notable changes to DevPulseAI are documented here.

---

## [3.0.0] — 2026-02-23 (feat/v3)

### ⚡ v2 → v3 — What Changed

> v2 was a Streamlit prototype with a single LLM agent and REST scrapers.
> v3 is a cloud-native intelligence platform with a FastAPI backend, multi-agent swarm, MCP servers, and a React frontend.

---

### 🏗 Architecture — Complete Rewrite

| Aspect | v2 | v3 |
|---|---|---|
| **Backend** | Streamlit (monolithic) | FastAPI (17 endpoints + WebSocket) |
| **Frontend** | Streamlit widgets only | React + Vite + TypeScript + Tailwind v4 |
| **Agents** | 1 general-purpose LLM call | 9 specialized agents in a MultiSwarm pipeline |
| **Data Sources** | 2 REST scrapers (GitHub, ArXiv) | 5 adapters (GitHub, ArXiv, HackerNews, Medium, HuggingFace) |
| **External APIs** | Direct HTTP calls | 4 MCP servers (GitHub, HuggingFace, Supabase, Pinecone) |
| **Storage** | In-memory only | Supabase (8 tables + RLS) + Pinecone (vector search) |
| **LLM Strategy** | Single model, no cost tracking | 3-tier cost-aware routing (fast/mid/strong) |
| **Chat** | Streamlit `st.chat_input` | WebSocket streaming + REST fallback |
| **Alerts** | None | Discord, Slack, Email (severity-based dispatch) |
| **Deployment** | `streamlit run` | Docker + Render + `/ping` health check |

---

### 🆕 Added in v3

#### Multi-Agent Swarm System (`app/agents/`)

- **Researcher** — GitHub repo deep-dives via MCP
- **Analyst** — ArXiv paper summarization and analysis
- **ProjectExplorer** — Local codebase scanning, dependency graph builder
- **CommunityVibeAgent** — Lexicon-based sentiment from HackerNews + signals
- **RiskAnalyst** — CVE scanner with codebase cross-reference
- **DependencyImpactAnalyzer** — Dependency update impact tracing
- **Critic** — Self-correction loop, hallucination gating
- **TrendDetector** — Emerging pattern identification across sources
- **MultiSwarm Orchestrator** — Parallel task routing, fan-out coordination (`app/core/swarm.py`)

#### MCP Server Integration (`mcp_config.json`)

- **GitHub MCP** — `search_repositories`, `get_file_contents`, `search_code`
- **HuggingFace MCP** — `hub_repo_search`, `paper_search`, `space_search`
- **Supabase MCP** — `execute_sql`, `apply_migration`, 8 persistent tables
- **Pinecone MCP** — `search-records`, `upsert-records`, `devpulseai-knowledge` index

#### FastAPI Backend (`app/api/server.py`)

- 17 REST/WebSocket endpoints
- `WebSocket /ws/chat` — real-time streaming chat with MultiSwarm
- `POST /api/chat` — REST fallback (non-streaming)
- `POST /api/feedback` — 👍/👎 feedback → Supabase `user_feedback` table
- `GET /api/signals` — query raw signals with source filtering
- `GET /api/intelligence` — query processed intelligence by agent
- `GET /api/conversations/{id}` — conversation history retrieval
- `GET /api/recommendations` — Pinecone-powered proactive suggestions
- `POST /api/context` — scan project deps, build codebase context
- `GET /api/model-router/status` — model routing config + cost tracking
- `GET /api/alerts/status` — alert system config + dispatch history
- `POST /ingest` — trigger ingestion from a specific source
- `POST /daily-pulse` — full pipeline: ingest → process → store → alert
- `GET /ping` — health check for Render keep-alive

#### Codebase-Aware Intelligence (`app/core/codebase_context.py`)

- Parses `requirements.txt`, `package.json`, `pyproject.toml`
- Builds project dependency graph (direct + framework detection)
- Scores every signal against user's actual tech stack (0.0 – 1.0)

#### Vector Knowledge Graph (`app/core/knowledge_graph.py`)

- Entity extraction: Repositories, Papers, Libraries, Concepts, Authors
- Edge types: `inspired-by`, `contradicts`, `forked-from`, `depends-on`
- Entities indexed in Pinecone, edges stored in Supabase `knowledge_edges`

#### Cost-Aware Model Routing (`app/core/model_router.py`)

- 3-tier LLM selection: `fast` (gpt-4.1-mini), `mid` (gpt-4.1-mini), `strong` (gpt-4.1)
- Per-call cost tracking with token-level accounting
- Configurable via `MODEL_FAST`, `MODEL_MID`, `MODEL_STRONG` env vars

#### Proactive Alert System (`app/core/alerts.py`)

- Severity-based dispatch: `CRITICAL` (CVE), `HIGH` (breaking change), `MEDIUM`, `LOW`
- **Discord** — rich embed webhooks
- **Slack** — Block Kit formatted messages
- **Email** — via Resend API
- Auto-triggered during ingestion pipeline

#### Signal Adapters (5 sources)

- `adapters/github.py` — trending repos (24h), stars, languages
- `adapters/arxiv.py` — latest AI/ML papers, abstracts
- `adapters/hackernews.py` — top stories, points, comments
- `adapters/medium.py` — AI/ML blog RSS feeds
- `adapters/huggingface.py` — trending models, daily papers, popular Spaces

#### Supabase Persistence (`app/core/persistence.py`)

- 8 tables: `raw_signals`, `processed_intelligence`, `conversations`, `messages`, `user_feedback`, `agent_traces`, `knowledge_entities`, `knowledge_edges`
- Row Level Security (RLS) policies
- Full source traceability: signal → intelligence → agent trace

#### React Frontend (`ui/devpulseai-ui-main/`)

- **Vite + React 19 + TypeScript + Tailwind CSS v4**
- 6 pages: Landing, Chat, Dashboard, Agents, Signals, Settings
- Real WebSocket chat with auto-reconnect (exponential backoff)
- Dashboard with live signal feed, intelligence cards, distribution charts
- Signal explorer with source filtering, search, pagination
- Settings page with model tier display, alert channels, project scan
- "Midnight Teal" dark design system with glassmorphism
- Vite proxy to FastAPI backend (dev), static server (prod)

#### Recommendation Engine (`app/core/recommendations.py`)

- Pinecone-backed semantic similarity
- Context-aware suggestions based on conversation history
- Surfaced in Chat sidebar and Dashboard

---

### ♻️ Changed from v2

- **Streamlit UI** (`app/ui/chat.py`) retained for backward compatibility but superseded by React frontend
- **Signal models** rewritten with strict Pydantic validation (`Signal`, `ProcessedIntelligence`)
- **Conversation pipeline** refactored from single-shot to multi-turn with memory
- **Configuration** moved from hardcoded values to environment variables (`.env`)
- **Logging** centralized via `app/core/logger.py` with structured output

---

### 🗑 Removed from v2

- In-memory-only signal storage (replaced by Supabase + Pinecone)
- Direct REST scraping (replaced by MCP servers)
- Single LLM call architecture (replaced by MultiSwarm)
- Basic Streamlit-only chat (WebSocket + React now primary)
- Mock API routes in UI server.ts (replaced by real backend proxy)

---

### 📊 By the Numbers

| Metric | v2 | v3 |
|---|---|---|
| Python files | ~8 | 40+ |
| API endpoints | 0 (Streamlit only) | 17 |
| Agent types | 1 | 9 |
| Signal sources | 2 | 5 |
| MCP integrations | 0 | 4 |
| Database tables | 0 | 8 |
| Frontend framework | Streamlit | React + Vite |
| WebSocket support | No | Yes |
| Cost tracking | No | Per-call token accounting |
| Alert channels | 0 | 3 (Discord, Slack, Email) |
| Vector search | No | Pinecone (multilingual-e5-large) |

---

## [2.0.0] — 2025-12 (master)

### Overview

DevPulseAI v2 was the initial prototype — a Streamlit-based dashboard that fetched signals from GitHub and ArXiv, processed them through a single OpenAI LLM call, and displayed results in a chat-like interface.

### Features

- **Streamlit Dashboard** — 4 tabs: Chat, Dashboard, Agents, Signal Feed
- **Signal Ingestion** — GitHub trending repos + ArXiv papers via REST APIs
- **Single-Agent Processing** — One OpenAI call per signal batch
- **In-Memory Storage** — All data lost on restart
- **Basic Chat** — `st.chat_input` with synchronous LLM responses
- **Plotly Gauges** — Confidence visualization for agent status
- **Custom CSS** — Dark theme with teal accents in Streamlit

### Limitations (addressed in v3)

- No persistent storage — everything in-memory
- No real-time streaming — synchronous Streamlit reruns
- Single agent — no specialization or parallel processing
- No cost tracking — uncontrolled API spend
- No alerting — manual checking only
- No codebase awareness — generic signal scoring
- No vector search — keyword matching only
- 2 signal sources only — GitHub and ArXiv

---

## [1.0.0] — 2025-11

Initial concept. Signal aggregation scripts with basic terminal output.
