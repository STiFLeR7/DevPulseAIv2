"""
Migration: Create project_context table in Supabase (SOW §5)

Run once:
    python -m scripts.migrate_project_context

This creates the table used by Codebase-Aware Intelligence to store
parsed dependency graphs for each user project.
"""

import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")


SQL = """
CREATE TABLE IF NOT EXISTS project_context (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'requirements.txt',
    content_hash TEXT NOT NULL,
    dependencies JSONB NOT NULL DEFAULT '{}',
    dev_dependencies JSONB NOT NULL DEFAULT '{}',
    languages TEXT[] DEFAULT '{}',
    frameworks TEXT[] DEFAULT '{}',
    ecosystems TEXT[] DEFAULT '{}',
    tech_tags TEXT[] DEFAULT '{}',
    last_updated TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_name, source_type)
);

ALTER TABLE project_context ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'project_context' AND policyname = 'Allow all for service role'
    ) THEN
        CREATE POLICY "Allow all for service role" ON project_context
            FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

COMMENT ON TABLE project_context IS 'Stores parsed project dependency context for codebase-aware signal scoring (SOW §5)';
"""


def run():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Set SUPABASE_URL and SUPABASE_KEY/SUPABASE_SERVICE_KEY env vars")
        return

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("🔄 Creating project_context table...")

    try:
        sb.postgrest.rpc("exec_sql", {"query": SQL}).execute()
        print("✅ project_context table created")
    except Exception as e:
        # Fallback: try direct REST
        print(f"⚠️  RPC method not available ({e}), try running SQL directly in Supabase dashboard:")
        print(SQL)


if __name__ == "__main__":
    run()
