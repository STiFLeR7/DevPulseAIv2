"""
Test: Ephemeral Worker Agents (SOW §3)

Verifies:
  1. CommunityVibeAgent — sentiment analysis
  2. RiskAnalyst — CVE/breaking change detection
  3. DependencyImpactAnalyzer — dependency chain impact
  4. ModelRouter — tier selection & cost estimation
  5. AlertDispatcher — channel config & dispatch logging
"""

import asyncio
import time

start = time.time()


# ── 1. CommunityVibeAgent ─────────────────────────

from app.agents.community_vibe import CommunityVibeAgent

vibe = CommunityVibeAgent()
assert vibe.name == "CommunityVibeAgent"

# Test topic extraction
topic = vibe._extract_topic("What's the community vibe on Rust?")
assert topic == "rust", f"Expected 'rust', got '{topic}'"

topic2 = vibe._extract_topic("sentiment on PyTorch lately?")
assert "pytorch" in topic2.lower(), f"Expected 'pytorch' in '{topic2}'"

# Test sentiment analysis
signals = [
    {"title": "Rust is amazing for systems programming", "content": "Fast, safe, and efficient"},
    {"title": "Rust has a steep learning curve", "content": "The borrow checker is terrible"},
    {"title": "Rust 2024 update looks great", "content": "New features are impressive"},
]
analysis = vibe._analyze_sentiment(signals, "rust")
assert analysis["vibe"] in ("positive", "mixed", "negative"), f"Invalid vibe: {analysis['vibe']}"
assert isinstance(analysis["positive_ratio"], float)
assert len(analysis["themes"]) > 0

# Test summary building
summary = vibe._build_summary("Rust", analysis)
assert "Rust" in summary
assert any(emoji in summary for emoji in ["🟢", "🟡", "🔴"])
print(f"  ✓ CommunityVibeAgent: topic extraction + sentiment + summary")


# ── 2. RiskAnalyst ────────────────────────────────

from app.agents.risk_analyst import RiskAnalyst

risk = RiskAnalyst()
assert risk.name == "RiskAnalyst"

# Test CVE pattern detection
import re
matches = RiskAnalyst.CVE_PATTERN.findall("Found CVE-2024-12345 and CVE-2025-99999")
assert len(matches) == 2, f"Expected 2 CVEs, got {len(matches)}"

# Test risk scanning with mock signals
mock_signals = [
    {"source": "nvd", "payload": {
        "title": "CVE-2025-12345: Critical vulnerability in httpx",
        "content": "Remote code execution in httpx < 0.28.0"
    }},
    {"source": "hackernews", "payload": {
        "title": "FastAPI 1.0 breaking changes",
        "content": "Breaking change: middleware API deprecated and removed"
    }},
    {"source": "hackernews", "payload": {
        "title": "New React 20 features",
        "content": "Exciting new concurrent rendering improvements"
    }},
]

mock_context = {
    "project_name": "DevPulseAIv2",
    "dependencies": {"httpx": ">=0.27", "fastapi": ">=0.115"},
}

risks = risk._scan_risks(mock_signals, mock_context)
assert len(risks) >= 2, f"Expected ≥2 risks, got {len(risks)}"

# CVE should be first (CRITICAL)
cve_risks = [r for r in risks if r["type"] == "cve"]
assert len(cve_risks) >= 1, "No CVE risks detected"
assert cve_risks[0]["severity"] == "CRITICAL"
assert "httpx" in cve_risks[0].get("affected_deps", [])

# Breaking change should be detected
breaking = [r for r in risks if r["type"] == "breaking_change"]
assert len(breaking) >= 1, "No breaking change risks detected"

print(f"  ✓ RiskAnalyst: CVE detection + breaking changes + project impact")


# ── 3. DependencyImpactAnalyzer ───────────────────

from app.agents.dependency_impact import DependencyImpactAnalyzer

dep = DependencyImpactAnalyzer()
assert dep.name == "DependencyImpactAnalyzer"

# Test dependency extraction
dep_name = dep._extract_dependency("What's the impact of updating httpx?")
assert dep_name == "httpx", f"Expected 'httpx', got '{dep_name}'"

dep_name2 = dep._extract_dependency("impact of fastapi upgrade")
assert "fastapi" in dep_name2.lower(), f"Expected 'fastapi', got '{dep_name2}'"

# Test impact analysis
mock_ctx = {
    "dependencies": {"httpx": ">=0.27", "fastapi": ">=0.115"},
    "dev_dependencies": {"pytest": ">=8.0"},
    "frameworks": ["fastapi"],
    "tech_tags": ["async", "api"],
}

impact = dep._analyze_impact("fastapi", mock_ctx)
assert impact["is_direct_dep"] is True
assert impact["risk_level"] == "HIGH"  # Framework = HIGH
assert "API/Web Layer" in impact["affected_areas"]

impact2 = dep._analyze_impact("pytest", mock_ctx)
assert impact2["is_dev_dep"] is True
assert impact2["risk_level"] == "LOW"

impact3 = dep._analyze_impact("nonexistent-lib", mock_ctx)
assert impact3["risk_level"] == "NONE"

print(f"  ✓ DependencyImpactAnalyzer: dep extraction + impact analysis + risk levels")


# ── 4. ModelRouter ────────────────────────────────

from app.core.model_router import ModelRouter

router = ModelRouter()
assert router.get_model("fast") == "gpt-4.1-mini"
assert router.get_model("strong") == "gpt-4.1"

cost = router.estimate_cost("gpt-4.1", 10000, 5000)
assert cost > 0, f"Cost should be positive, got {cost}"
assert cost < 1.0, f"Cost for 10k tokens should be < $1, got {cost}"

print(f"  ✓ ModelRouter: tier selection + cost estimation (10k tokens = ${cost})")


# ── 5. AlertDispatcher ────────────────────────────

from app.core.alerts import AlertDispatcher, AlertType

dispatcher = AlertDispatcher()

# Without env vars, no channels should be configured
status = dispatcher.status()
assert isinstance(status["configured_channels"], list)
assert status["total_alerts_sent"] == 0

print(f"  ✓ AlertDispatcher: initialization + status check")


# ── Summary ───────────────────────────────────────

elapsed = time.time() - start
print(f"\n{'='*60}")
print(f"[OK] All ephemeral workers verified in {elapsed:.2f}s")
print(f"{'='*60}")
