"""
Migration: Create knowledge_edges table in Supabase (SOW §4.1)

Run once:
    python -m scripts.migrate_knowledge_edges

Stores directed edges between entities for the Vector Knowledge Graph.
"""

SQL = """
CREATE TABLE IF NOT EXISTS knowledge_edges (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(source_id, target_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_edges_source ON knowledge_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON knowledge_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_relation ON knowledge_edges(relation_type);

ALTER TABLE knowledge_edges ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'knowledge_edges' AND policyname = 'Allow all for service role'
    ) THEN
        CREATE POLICY "Allow all for service role" ON knowledge_edges
            FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

COMMENT ON TABLE knowledge_edges IS 'Directed edges between entities in the Vector Knowledge Graph (SOW §4.1)';
"""


def run():
    import os
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ Set SUPABASE_URL and SUPABASE_KEY env vars")
        print("\nAlternatively, run this SQL in the Supabase dashboard:")
        print(SQL)
        return

    sb = create_client(url, key)
    print("🔄 Creating knowledge_edges table...")

    try:
        sb.postgrest.rpc("exec_sql", {"query": SQL}).execute()
        print("✅ knowledge_edges table created")
    except Exception as e:
        print(f"⚠️  RPC not available ({e})")
        print("\nRun this SQL in the Supabase SQL Editor:")
        print(SQL)


if __name__ == "__main__":
    run()
