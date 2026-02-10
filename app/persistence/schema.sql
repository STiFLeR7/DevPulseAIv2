-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Agent Traces (Observability)
-- Stores execution logs, reasoning steps, and tool calls for the swarm.
CREATE TABLE IF NOT EXISTS agent_traces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL, -- Correlates multiple steps in a single workflow run
    agent_name TEXT NOT NULL, -- e.g., "LeadResearcher", "RepoDiver"
    step_name TEXT NOT NULL, -- e.g., "Search", "Reason", "Synthesize"
    input_state JSONB, -- The input context for this step
    output_state JSONB, -- The output produced by this step
    tool_calls JSONB, -- Array of tool calls made during this step
    model_name TEXT, -- The LLM used (e.g., "gemini-1.5-flash")
    prompt_tokens INT,
    completion_tokens INT,
    latency_ms INT,
    status TEXT CHECK (status IN ('running', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast retrieval of traces by run_id
CREATE INDEX IF NOT EXISTS idx_agent_traces_run_id ON agent_traces(run_id);
CREATE INDEX IF NOT EXISTS idx_agent_traces_status ON agent_traces(status);

-- 2. User Feedback (Human-in-the-Loop)
-- Stores user votes on specific signals or insights to fine-tune relevance.
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id TEXT NOT NULL, -- External ID of the signal (e.g., GitHub URL or ArXiv ID)
    user_id UUID, -- If auth is enabled later
    vote_type TEXT CHECK (vote_type IN ('relevant', 'irrelevant', 'useful', 'noise')),
    feedback_text TEXT, -- Optional unstructured feedback
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for analytics on helpfulness
CREATE INDEX IF NOT EXISTS idx_user_feedback_signal ON user_feedback(signal_id);

-- 3. Project Context (Personalization)
-- Stores the dependency graph and tech stack profile of the user.
CREATE TABLE IF NOT EXISTS project_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_name TEXT NOT NULL,
    source_type TEXT NOT NULL, -- e.g., "requirements.txt", "package.json"
    content_hash TEXT NOT NULL, -- For change detection
    dependencies JSONB NOT NULL, -- Structured list of libs: {"name": "fastapi", "version": "^0.100"}
    tech_tags TEXT[], -- Derived tags: ["python", "web", "async"]
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Knowledge Graph Relations (Metadata for Vector Store)
-- Though vectors live in Pinecone, we store structured relations here for hybrid search.
CREATE TABLE IF NOT EXISTS knowledge_relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_entity_id TEXT NOT NULL, -- e.g., "paper:1234.5678"
    target_entity_id TEXT NOT NULL, -- e.g., "repo:github.com/user/repo"
    relation_type TEXT NOT NULL, -- e.g., "implements", "cites", "contradicts"
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_rel_source ON knowledge_relations(source_entity_id);
