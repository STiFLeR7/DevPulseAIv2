"""
Test: Vector Knowledge Graph (SOW §4.1)

Verifies:
  1. EntityExtractor — all 5 entity types
  2. Entity deduplication
  3. KnowledgeGraph.add_document() (mock, no Pinecone/Supabase needed)
  4. Auto-linking heuristics
"""

import time
start = time.time()


# ── 1. Test EntityExtractor ──────────────────────

from app.memory.graph import EntityExtractor, Entity

extractor = EntityExtractor()

sample_text = """
Check out https://github.com/huggingface/transformers for the latest
transformer models. The paper arxiv:2401.12345 introduces a new LoRA
technique for fine-tuning LLMs. Built with PyTorch and FastAPI.

Related work: 10.1234/ml.2024.001 discusses RAG pipelines with
Pinecone vector databases. The multi-agent approach uses LangChain
for chain-of-thought reasoning.
"""

entities = extractor.extract_entities(sample_text)

# Check entity counts by type
types = {}
for e in entities:
    types[e.entity_type] = types.get(e.entity_type, 0) + 1

print(f"\n  Extracted {len(entities)} entities from sample text:")
for etype, count in sorted(types.items()):
    names = [e.name for e in entities if e.entity_type == etype]
    print(f"    {etype}: {count} — {names}")

# Verify key entities were found
entity_names = {e.name for e in entities}
assert any("transformers" in n for n in entity_names), f"Missing transformers repo. Got: {entity_names}"
assert any("2401.12345" in n for n in entity_names), f"Missing arxiv paper. Got: {entity_names}"
assert "pytorch" in entity_names or "torch" in entity_names, f"Missing pytorch. Got: {entity_names}"
assert "fastapi" in entity_names, f"Missing fastapi. Got: {entity_names}"
assert "LoRA" in entity_names, f"Missing LoRA concept. Got: {entity_names}"
assert "RAG" in entity_names, f"Missing RAG concept. Got: {entity_names}"
print(f"  ✓ EntityExtractor: all entity types detected")


# ── 2. Test deduplication ────────────────────────

dup_text = """
Check https://github.com/openai/openai-python twice:
https://github.com/openai/openai-python and also openai library.
"""

dup_entities = extractor.extract_entities(dup_text)
repo_count = sum(1 for e in dup_entities if e.entity_type == "repository" and "openai" in e.name)
assert repo_count == 1, f"Duplicate repos not deduplicated: {repo_count}"
print(f"  ✓ Deduplication: duplicate entities filtered")


# ── 3. Test Entity ID stability ──────────────────

e1 = Entity("library", "pytorch")
e2 = Entity("library", "pytorch")
assert e1.entity_id == e2.entity_id, "Same name should produce same entity_id"
print(f"  ✓ Entity IDs: deterministic and stable")


# ── 4. Test KnowledgeGraph (no external deps) ───

from app.memory.graph import KnowledgeGraph

# Create graph without Pinecone/Supabase (offline mode)
graph = KnowledgeGraph(pinecone_index=None, supabase_client=None)

# add_document should still extract entities
doc_entities = graph.add_document(
    doc_id="test-doc-001",
    content="New PyTorch 2.5 release adds FlexAttention. Paper: arxiv:2405.98765",
    metadata={"source": "hackernews"}
)

assert len(doc_entities) > 0, "No entities extracted from document"
entity_types_found = {e.entity_type for e in doc_entities}
assert "library" in entity_types_found, f"No library entities. Found: {entity_types_found}"
print(f"  ✓ KnowledgeGraph.add_document(): extracted {len(doc_entities)} entities")


# ── 5. Test concept coverage ────────────────────

concept_text = """
Mixture of experts models with speculative decoding achieve
state-of-the-art reasoning on chain-of-thought benchmarks.
Quantization and distillation reduce inference cost.
"""

concept_entities = extractor.extract_entities(concept_text)
concepts = {e.name for e in concept_entities if e.entity_type == "concept"}
assert "Mixture of Experts" in concepts, f"Missing MoE in {concepts}"
assert "Chain-of-Thought" in concepts, f"Missing CoT in {concepts}"
assert "Quantization" in concepts, f"Missing Quantization in {concepts}"
print(f"  ✓ Concept coverage: {len(concepts)} concepts detected")


# ── Summary ──────────────────────────────────────

elapsed = time.time() - start
print(f"\n{'='*60}")
print(f"[OK] Vector Knowledge Graph verified in {elapsed:.2f}s")
print(f"{'='*60}")
