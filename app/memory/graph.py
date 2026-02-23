"""
Vector Knowledge Graph — SOW §4.1

Historical reasoning, not just retrieval.

Entity extraction via regex patterns → entities stored in Pinecone with
type-aware metadata → relation edges stored in Supabase knowledge_edges table.

Entity types:
  - Repository  (GitHub URLs)
  - Paper       (ArXiv IDs, DOIs)
  - Library     (package names from deps/imports)
  - Author      (contributor names)
  - Concept     (AI/ML keywords)

Relation types:
  - uses           (repo → library)
  - inspired-by    (paper → paper)
  - contradicts    (paper → paper)
  - forked-from    (repo → repo)
  - evolution-of   (library → library)
  - impacts        (cve → library)
"""

import re
import hashlib
import datetime
from typing import List, Dict, Any, Optional, Tuple

from app.core.logger import logger


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Entity Types
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENTITY_TYPES = {
    "repository", "paper", "library", "author", "concept"
}

RELATION_TYPES = {
    "uses", "inspired-by", "contradicts", "forked-from",
    "evolution-of", "impacts", "authored-by", "related-to"
}

# Regex patterns for entity extraction
GITHUB_URL_PATTERN = re.compile(
    r'(?:https?://)?github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)', re.IGNORECASE
)

ARXIV_ID_PATTERN = re.compile(
    r'(?:arxiv[:\s]*)?(\d{4}\.\d{4,5}(?:v\d+)?)', re.IGNORECASE
)

DOI_PATTERN = re.compile(
    r'10\.\d{4,9}/[^\s,]+', re.IGNORECASE
)

# Common AI/ML concept keywords → canonical names
CONCEPT_KEYWORDS = {
    "transformer": "Transformer",
    "attention": "Attention Mechanism",
    "rag": "RAG",
    "retrieval-augmented": "RAG",
    "retrieval augmented": "RAG",
    "rlhf": "RLHF",
    "reinforcement learning from human feedback": "RLHF",
    "fine-tuning": "Fine-Tuning",
    "fine tuning": "Fine-Tuning",
    "lora": "LoRA",
    "qlora": "QLoRA",
    "diffusion": "Diffusion Model",
    "embedding": "Embeddings",
    "vector database": "Vector Database",
    "knowledge graph": "Knowledge Graph",
    "multi-agent": "Multi-Agent",
    "agent swarm": "Agent Swarm",
    "chain-of-thought": "Chain-of-Thought",
    "reasoning": "Reasoning",
    "tool-use": "Tool Use",
    "function calling": "Function Calling",
    "mcp": "MCP Protocol",
    "model context protocol": "MCP Protocol",
    "cve": "CVE",
    "vulnerability": "Security Vulnerability",
    "llm": "Large Language Model",
    "vision model": "Vision Model",
    "multimodal": "Multimodal",
    "mixture of experts": "Mixture of Experts",
    "moe": "Mixture of Experts",
    "speculative decoding": "Speculative Decoding",
    "quantization": "Quantization",
    "distillation": "Distillation",
}

# Common Python/JS package names to detect in text
KNOWN_LIBRARIES = {
    "pytorch", "torch", "tensorflow", "jax", "numpy", "pandas",
    "fastapi", "flask", "django", "streamlit", "gradio",
    "transformers", "huggingface", "langchain", "llamaindex",
    "openai", "anthropic", "gemini", "mistral", "cohere",
    "pinecone", "supabase", "redis", "postgres", "mongodb",
    "react", "nextjs", "next.js", "vue", "angular", "svelte",
    "docker", "kubernetes", "celery", "ray", "dask",
    "scikit-learn", "scipy", "matplotlib", "plotly",
    "agno", "crewai", "autogen", "dspy",
    "vllm", "ollama", "litellm", "lmstudio",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Entity Extractor
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Entity:
    """A single extracted entity."""

    def __init__(self, entity_type: str, name: str, source_text: str = "",
                 confidence: float = 1.0, metadata: Dict = None):
        self.entity_type = entity_type
        self.name = name
        self.source_text = source_text
        self.confidence = confidence
        self.metadata = metadata or {}
        self.entity_id = self._generate_id()

    def _generate_id(self) -> str:
        """Deterministic ID from type + name."""
        key = f"{self.entity_type}:{self.name}".lower()
        return hashlib.md5(key.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "name": self.name,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class EntityExtractor:
    """
    Extracts structured entities from raw text using regex patterns.

    No LLM dependency — fast, deterministic, auditable.
    """

    def extract_entities(self, content: str, source_type: str = "unknown") -> List[Entity]:
        """
        Extract all entity types from text content.
        Returns deduplicated entities sorted by confidence.
        """
        entities = []
        seen_ids = set()

        # 1. GitHub repositories
        for match in GITHUB_URL_PATTERN.finditer(content):
            repo_name = match.group(1)
            e = Entity("repository", repo_name, match.group(0), confidence=0.95,
                        metadata={"url": f"https://github.com/{repo_name}"})
            if e.entity_id not in seen_ids:
                entities.append(e)
                seen_ids.add(e.entity_id)

        # 2. ArXiv papers
        for match in ARXIV_ID_PATTERN.finditer(content):
            arxiv_id = match.group(1)
            e = Entity("paper", f"arxiv:{arxiv_id}", match.group(0), confidence=0.9,
                        metadata={"arxiv_id": arxiv_id, "url": f"https://arxiv.org/abs/{arxiv_id}"})
            if e.entity_id not in seen_ids:
                entities.append(e)
                seen_ids.add(e.entity_id)

        # 3. DOIs
        for match in DOI_PATTERN.finditer(content):
            doi = match.group(0)
            e = Entity("paper", f"doi:{doi}", doi, confidence=0.85,
                        metadata={"doi": doi})
            if e.entity_id not in seen_ids:
                entities.append(e)
                seen_ids.add(e.entity_id)

        # 4. Known libraries
        content_lower = content.lower()
        for lib in KNOWN_LIBRARIES:
            # Match whole word to avoid false positives
            pattern = rf'\b{re.escape(lib)}\b'
            if re.search(pattern, content_lower):
                e = Entity("library", lib, "", confidence=0.8)
                if e.entity_id not in seen_ids:
                    entities.append(e)
                    seen_ids.add(e.entity_id)

        # 5. AI/ML concepts
        for keyword, canonical in CONCEPT_KEYWORDS.items():
            if keyword in content_lower:
                e = Entity("concept", canonical, keyword, confidence=0.7)
                if e.entity_id not in seen_ids:
                    entities.append(e)
                    seen_ids.add(e.entity_id)

        # Sort by confidence desc
        entities.sort(key=lambda e: e.confidence, reverse=True)

        return entities


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Knowledge Graph
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class KnowledgeGraph:
    """
    Hybrid Knowledge Graph: Pinecone (vectors) + Supabase (edges).

    - Entities stored as Pinecone records with type-aware metadata
    - Edges stored in Supabase knowledge_edges table for traversal
    - Supports entity linking, relation queries, and graph traversal
    """

    def __init__(self, pinecone_index=None, supabase_client=None):
        self.pinecone_index = pinecone_index
        self.supabase = supabase_client
        self.extractor = EntityExtractor()

        # Initialize Pinecone if not provided
        if not self.pinecone_index:
            try:
                from pinecone import Pinecone
                import os
                pc_key = os.environ.get("PINECONE_API_KEY")
                if pc_key:
                    pc = Pinecone(api_key=pc_key)
                    self.pinecone_index = pc.Index("devpulseai-knowledge")
            except Exception:
                pass

        # Initialize Supabase if not provided
        if not self.supabase:
            try:
                from app.persistence.client import db
                self.supabase = db.get_client()
            except Exception:
                pass

    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None) -> List[Entity]:
        """
        Add a document to the knowledge graph:
        1. Extract entities from content
        2. Store each entity in Pinecone with type metadata
        3. Link entities to the document via edges

        Returns extracted entities.
        """
        metadata = metadata or {}
        source = metadata.get("source", "unknown")

        # Extract entities
        entities = self.extractor.extract_entities(content, source)

        if not entities:
            return []

        # Store entities in Pinecone
        if self.pinecone_index:
            records = []
            for entity in entities:
                records.append({
                    "_id": entity.entity_id,
                    "content": f"{entity.entity_type}: {entity.name}",
                    "entity_type": entity.entity_type,
                    "name": entity.name,
                    "confidence": entity.confidence,
                    "source_doc": doc_id,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    **entity.metadata,
                })

            try:
                self.pinecone_index.upsert_records(
                    namespace="entities",
                    records=records,
                )
                logger.info(f"KnowledgeGraph: Stored {len(records)} entities for doc {doc_id}")
            except Exception as e:
                logger.warning(f"KnowledgeGraph: Pinecone upsert failed: {e}")

        # Create edges: document → entity
        for entity in entities:
            self.link_entities(
                source_id=doc_id,
                target_id=entity.entity_id,
                relation_type="contains",
                confidence=entity.confidence,
            )

        # Auto-link entities within the same document
        self._auto_link_entities(entities, doc_id)

        return entities

    def link_entities(self, source_id: str, target_id: str,
                      relation_type: str, confidence: float = 1.0):
        """
        Create a directed edge between two entities.
        Stored in Supabase knowledge_edges table.
        """
        if not self.supabase:
            return

        try:
            self.supabase.table("knowledge_edges").upsert({
                "source_id": source_id,
                "target_id": target_id,
                "relation_type": relation_type,
                "confidence": confidence,
            }, on_conflict="source_id, target_id, relation_type").execute()
        except Exception as e:
            logger.warning(f"KnowledgeGraph: Edge insert failed: {e}")

    def _auto_link_entities(self, entities: List[Entity], doc_id: str):
        """
        Auto-detect relationships between co-occurring entities.

        Heuristics:
        - repository + library → "uses" relation
        - paper + concept → "related-to" relation
        - concept + concept → "related-to" relation (co-occurrence)
        """
        repos = [e for e in entities if e.entity_type == "repository"]
        libs = [e for e in entities if e.entity_type == "library"]
        papers = [e for e in entities if e.entity_type == "paper"]
        concepts = [e for e in entities if e.entity_type == "concept"]

        # Repos use libraries
        for repo in repos:
            for lib in libs:
                self.link_entities(repo.entity_id, lib.entity_id, "uses", 0.7)

        # Papers relate to concepts
        for paper in papers:
            for concept in concepts:
                self.link_entities(paper.entity_id, concept.entity_id, "related-to", 0.6)

        # Co-occurring concepts are related
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i+1:]:
                self.link_entities(c1.entity_id, c2.entity_id, "related-to", 0.5)

    def query_related(self, entity_name: str, limit: int = 10) -> List[Dict]:
        """
        Find entities related to a given entity name.
        Searches Pinecone for semantically similar entities.
        """
        if not self.pinecone_index:
            return []

        try:
            results = self.pinecone_index.search(
                namespace="entities",
                query={"inputs": {"text": entity_name}, "top_k": limit},
            )
            return [
                {
                    "id": hit.get("_id"),
                    "score": hit.get("_score", 0),
                    **hit.get("fields", {}),
                }
                for hit in results.get("result", {}).get("hits", [])
            ]
        except Exception as e:
            logger.warning(f"KnowledgeGraph: Query failed: {e}")
            return []

    def get_edges(self, entity_id: str, direction: str = "outgoing") -> List[Dict]:
        """
        Get edges for an entity from Supabase.
        direction: 'outgoing' (source), 'incoming' (target), or 'both'
        """
        if not self.supabase:
            return []

        edges = []
        try:
            if direction in ("outgoing", "both"):
                result = self.supabase.table("knowledge_edges").select("*").eq(
                    "source_id", entity_id
                ).execute()
                edges.extend(result.data or [])

            if direction in ("incoming", "both"):
                result = self.supabase.table("knowledge_edges").select("*").eq(
                    "target_id", entity_id
                ).execute()
                edges.extend(result.data or [])
        except Exception as e:
            logger.warning(f"KnowledgeGraph: Edge query failed: {e}")

        return edges
