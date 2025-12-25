-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Raw Signals Table
-- Stores the immutable snapshot of data ingested from external sources.
CREATE TABLE IF NOT EXISTS raw_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source TEXT NOT NULL, -- 'github', 'huggingface', 'medium', 'rss'
    external_id TEXT NOT NULL, -- Unique ID from the source (e.g., URL or Git hash)
    payload JSONB NOT NULL, -- The full raw data object
    content_hash TEXT NOT NULL, -- SHA256 of the payload for deduplication
    UNIQUE(source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_signals_content_hash ON raw_signals(content_hash);
CREATE INDEX IF NOT EXISTS idx_raw_signals_created_at ON raw_signals(created_at);

-- 2. Processed Intelligence Table
-- Stores the output of agents (summaries, scores, risks).
CREATE TABLE IF NOT EXISTS processed_intelligence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID REFERENCES raw_signals(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    agent_name TEXT NOT NULL, -- 'summarization', 'risk', 'trend', 'relevance'
    agent_version TEXT NOT NULL, -- version/model identifier
    output_data JSONB NOT NULL, -- Structured output (e.g., {summary: "...", score: 0.9})
    UNIQUE(signal_id, agent_name, agent_version)
);

-- 3. Audit Logs Table
-- Tracks system execution events for debugging and compliance.
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    component TEXT NOT NULL, -- 'ingestion', 'agent', 'inference', 'API'
    event_type TEXT NOT NULL, -- 'INFO', 'ERROR', 'WARNING'
    message TEXT NOT NULL,
    metadata JSONB -- Stack traces, request IDs, etc.
);

-- 4. Report History Table
-- Archives the daily digests generated for the user.
CREATE TABLE IF NOT EXISTS report_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    recipient TEXT NOT NULL,
    report_content TEXT NOT NULL, -- HTML or Markdown body
    status TEXT NOT NULL -- 'sent', 'failed'
);
