
# DevPulseAI v2: Autonomous Technical Intelligence System

![DevPulseAI Logo](assets/logo.png)

> **Automated Intelligence for the Modern Developer.**
> *Ingest. Analyze. Deliver.*

---

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## ⚡ Overview
**DevPulseAI v2** is a cloud-native, agentic intelligence platform designed to keep developers ahead of the curve. It autonomously aggregates signals from specific high-value sources, processes them through a multi-agent LLM pipeline (**Google Gemini 1.5 Flash**), and delivers a curated, color-coded daily digest directly to your inbox.

Unlike generic newsletters, DevPulseAI is **deterministic, verifiable, and highly specific** to your tech stack.

### 🏗 Architecture
The system follows a strict **Micro-Agent** architecture orchestrated via **FastAPI** and persistent state in **Supabase**.

```mermaid
graph TD
    A[Signal Sources] -->|Ingest| B(Ingestion Layer)
    B -->|Normalize| C{Supabase Raw Store}
    C -->|Trigger| D[Agent Swarm]
    D -->|Summarize| E[Gemini 1.5 Flash]
    D -->|Risk Analysis| E
    D -->|Trend Detect| E
    E -->|Structured Intel| F{Supabase Intelligence}
    F -->|Consolidate| G[Report Generator]
    G -->|SMTP| H[User Inbox]
    G -->|Web| I[Dashboard]
```

---

## 🧠 Core Features

### 1. Multi-Modal Ingestion
We treat every input as a "Signal". Adapters normalize diverse data streams into a unified schema.
*   **GitHub**: Trending Repositories & Release Notes.
*   **Hugging Face**: New Transformer Models & Datasets.
*   **ArXiv**: Latest AI/ML Research Papers.
*   **Medium**: Engineering Blogs (Netflix, Uber, Meta).
*   **X (Twitter)**: Key Opinion Leader (KOL) insights.

### 2. The "Tech Vibe" Daily Report
A highly styled, responsive HTML email that groups intelligence by category. No more wall of text.

| Category | Indicator | Description |
| :--- | :--- | :--- |
| **New Trends** | <img src="assets/new-trends.png" width="100"/> | Aggregated patterns (e.g., "Rise of SLMs"). |
| **New Repos** | <img src="assets/new-repos.png" width="100"/> | GitHub stars of the day (**Grey**). |
| **Updates** | <img src="assets/updates.png" width="100"/> | New Hugging Face models (**Yellow**). |
| **Insights** | <img src="assets/insights.png" width="100"/> | Deep dive ArXiv summaries (**Green**). |
| **Summary** | <img src="assets/summary.png" width="100"/> | Executive TL;DR of the day. |

### 3. Agentic Pipeline
Every signal passes through three specialized agents:
*   **Summarization Agent**: Condenses long-form content.
*   **Relevance Agent**: Scores 0-100 based on developer profile.
*   **Risk Agent**: Flags breaking changes or security vulnerabilities (HIGH/LOW).

---

## 🚀 Deployment (100% Free Stack)

### Option 1: One-Click Deploy (Recommended)
Click the button below to deploy this exact stack to **Render** (Free Tier).
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1.  Click the button.
2.  Connect your GitHub account.
3.  Fill in the **Environment Variables** (Supabase, Gemini, SMTP) when prompted.
4.  That's it!

### Option 2: Automate Trigger
Since the Free Tier "sleeps" after 15 mins of inactivity, use [Cron-Job.org](https://cron-job.org) to wake it up and send your report.
*   **URL**: `https://your-app.onrender.com/report`
*   **Method**: `POST`
*   **Schedule**: `Daily @ 08:00 AM` (IST is UTC+5:30, so set UTC to 02:30).

**Note**: GitHub Actions are **NOT** required. Render automatically redeploys whenever you push changes to the repository!

## 🛠 Local Development

```bash
# Clone the repo
git clone https://github.com/YourUsername/DevPulseAIv2.git

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.api.main:app --reload
```

## 📂 Directory Structure

```text
devpulse_v2/
├── app/
│   ├── agents/         # LLM Logic (Summary, Risk, Trend)
│   ├── adapters/       # GitHub, ArXiv, HF Scrapers
│   ├── api/            # FastAPI Endpoints
│   ├── core/           # Config & Logging
│   ├── reports/        # HTML Generation Engine
│   └── persistence/    # Supabase Client
├── scripts/            # Cron & Verification Scripts
├── Dockerfile          # Container Definition
└── requirements.txt    # Python Deps
```

---

> **Built with ❤️ by Hill Patel.**
> *Powered by Google Gemini & Supabase.*
