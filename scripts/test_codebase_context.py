"""
Test: Codebase-Aware Intelligence (SOW §5)

Verifies:
  1. requirements.txt parser
  2. package.json parser
  3. pyproject.toml parser
  4. CodebaseContextBuilder on DevPulseAIv2 itself
  5. Signal relevance scorer
"""

import sys
import time

start = time.time()

# ── 1. Test requirements.txt parser ──────────────

from app.core.codebase_context import parse_requirements_txt

sample_req = """
# Core
fastapi>=0.100
openai>=1.0
httpx
streamlit>=1.30

# ML
torch>=2.0
transformers
scikit-learn==1.3.0

# Dev
pytest
"""

deps, frameworks = parse_requirements_txt(sample_req)
assert "fastapi" in deps, f"Missing fastapi, got: {deps}"
assert "openai" in deps
assert "torch" in deps
assert deps["fastapi"] == ">=0.100"
assert deps["httpx"] == "*"
assert "fastapi" in frameworks
assert "torch" in frameworks
assert "transformers" in frameworks
print(f"  ✓ requirements.txt parser: {len(deps)} deps, {len(frameworks)} frameworks")


# ── 2. Test package.json parser ──────────────────

from app.core.codebase_context import parse_package_json

sample_pkg = """
{
  "name": "devpulse-ui",
  "dependencies": {
    "react": "^18.2.0",
    "next": "14.0.0",
    "@supabase/supabase-js": "^2.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "eslint": "^8.0.0"
  }
}
"""

deps, dev_deps, frameworks = parse_package_json(sample_pkg)
assert "react" in deps
assert "next" in deps
assert "typescript" in dev_deps
assert "react" in frameworks
assert "next" in frameworks
print(f"  ✓ package.json parser: {len(deps)} deps, {len(dev_deps)} dev, {len(frameworks)} frameworks")


# ── 3. Test pyproject.toml parser ────────────────

from app.core.codebase_context import parse_pyproject_toml

sample_pyproject = """
[project]
name = "devpulse"
version = "3.0.0"

dependencies = [
    "fastapi>=0.100",
    "openai>=1.0",
    "pinecone>=3.0",
]
"""

deps, frameworks = parse_pyproject_toml(sample_pyproject)
assert "fastapi" in deps
assert "openai" in deps
assert "pinecone" in deps
assert "fastapi" in frameworks
print(f"  ✓ pyproject.toml parser: {len(deps)} deps, {len(frameworks)} frameworks")


# ── 4. Test CodebaseContextBuilder on DevPulseAIv2 ─

from app.core.codebase_context import CodebaseContextBuilder

builder = CodebaseContextBuilder()
context = builder.build("D:/DevPulseAIv2")

print(f"\n  Project: {context.project_name}")
print(f"  Direct deps: {len(context.direct_deps)}")
print(f"  Languages: {context.languages}")
print(f"  Frameworks: {context.frameworks}")
print(f"  Tech tags: {context.tech_tags}")

assert len(context.direct_deps) > 0, "No deps found in DevPulseAIv2!"
assert "python" in context.languages
print(f"  ✓ CodebaseContextBuilder: {len(context.direct_deps)} deps from DevPulseAIv2")


# ── 5. Test signal relevance scorer ──────────────

from app.core.codebase_context import score_signal_relevance

# Signal that mentions a direct dependency → high relevance
score_high = score_signal_relevance(
    "FastAPI 0.115 released with breaking changes",
    "New validation in FastAPI affects existing route handlers",
    {"tags": ["api", "web"], "language": "python"},
    context
)

# Signal about unrelated tech → low relevance
score_low = score_signal_relevance(
    "New Flutter 4.0 released",
    "Dart 3.5 brings pattern matching improvements",
    {"tags": ["mobile", "dart"], "language": "dart"},
    context
)

# CVE signal mentioning a dep → critical boost
score_cve = score_signal_relevance(
    "CVE-2024-1234: httpx vulnerability found",
    "Remote code execution vulnerability in httpx HTTP client",
    {"tags": ["security", "cve"]},
    context
)

print(f"\n  Signal scores:")
print(f"    FastAPI update (should be HIGH):  {score_high:.2f}")
print(f"    Flutter release (should be LOW):  {score_low:.2f}")
print(f"    httpx CVE (should be CRITICAL):   {score_cve:.2f}")

assert score_high > score_low, f"FastAPI signal ({score_high}) should score higher than Flutter ({score_low})"
assert score_cve > score_high, f"CVE signal ({score_cve}) should score highest"
print(f"  ✓ Relevance scorer: HIGH({score_high:.2f}) > LOW({score_low:.2f}), CVE({score_cve:.2f}) is critical")


# ── Summary ──────────────────────────────────────

elapsed = time.time() - start
print(f"\n{'='*60}")
print(f"[OK] Codebase-Aware Intelligence verified in {elapsed:.2f}s")
print(f"{'='*60}")
