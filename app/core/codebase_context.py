"""
Codebase-Aware Intelligence — SOW §5

The primary differentiator of DevPulseAI v3.

Parses user's dependency files (requirements.txt, package.json, pyproject.toml),
builds a Project Context Graph, and scores incoming signals against it.

This transforms DevPulseAI from generic news → engineering situational awareness.

Example:
    A PyTorch paper scores higher if the user maintains vision models.
    A CVE scores CRITICAL if it affects a transitive dependency.
"""

import os
import re
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from app.core.logger import logger


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Project Context Model
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ProjectContext:
    """
    Parsed representation of a project's dependency graph and tech stack.
    Used for relevance scoring of incoming signals.
    """

    def __init__(
        self,
        project_name: str,
        direct_deps: Dict[str, str],
        dev_deps: Dict[str, str] = None,
        languages: List[str] = None,
        frameworks: List[str] = None,
        ecosystems: List[str] = None,
        tech_tags: List[str] = None,
    ):
        self.project_name = project_name
        self.direct_deps = direct_deps
        self.dev_deps = dev_deps or {}
        self.languages = languages or []
        self.frameworks = frameworks or []
        self.ecosystems = ecosystems or []
        self.tech_tags = tech_tags or []

    @property
    def all_deps(self) -> Dict[str, str]:
        """All dependencies (direct + dev)."""
        return {**self.direct_deps, **self.dev_deps}

    @property
    def dep_names(self) -> set:
        """Set of all dependency names (lowercased)."""
        return {k.lower() for k in self.all_deps}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "direct_deps": self.direct_deps,
            "dev_deps": self.dev_deps,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "ecosystems": self.ecosystems,
            "tech_tags": self.tech_tags,
        }

    def content_hash(self) -> str:
        """Deterministic hash for change detection."""
        payload = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Dependency Parsers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Known framework → tag mappings for auto-tagging
FRAMEWORK_TAGS = {
    "fastapi": ["api", "web", "async"],
    "flask": ["api", "web"],
    "django": ["web", "orm"],
    "streamlit": ["ui", "dashboard"],
    "gradio": ["ui", "ml-demo"],
    "torch": ["ml", "deep-learning", "pytorch"],
    "pytorch": ["ml", "deep-learning"],
    "tensorflow": ["ml", "deep-learning"],
    "transformers": ["nlp", "huggingface", "ml"],
    "langchain": ["llm", "ai", "rag"],
    "openai": ["llm", "ai", "gpt"],
    "agno": ["ai", "agents"],
    "pinecone": ["vector-db", "rag"],
    "supabase": ["database", "auth", "storage"],
    "httpx": ["http", "async"],
    "react": ["frontend", "ui"],
    "next": ["frontend", "ssr"],
    "vue": ["frontend", "ui"],
    "express": ["api", "node"],
    "prisma": ["orm", "database"],
    "pandas": ["data", "analytics"],
    "numpy": ["data", "scientific"],
    "scipy": ["scientific", "math"],
    "scikit-learn": ["ml", "classical-ml"],
    "celery": ["async", "task-queue"],
    "redis": ["cache", "database"],
    "docker": ["devops", "containers"],
}


def parse_requirements_txt(content: str) -> Tuple[Dict[str, str], List[str]]:
    """
    Parse a requirements.txt file content.
    Returns (deps_dict, detected_frameworks).
    """
    deps = {}
    frameworks = []

    for line in content.splitlines():
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        # Handle version specifiers: pkg>=1.0, pkg==1.0, pkg~=1.0, pkg!=1.0
        match = re.match(r'^([a-zA-Z0-9_.-]+)\s*([><=!~]+\s*[\d.*]+(?:\s*,\s*[><=!~]+\s*[\d.*]+)*)?', line)
        if match:
            pkg = match.group(1).lower().strip()
            version = (match.group(2) or "*").strip()
            deps[pkg] = version

            # Check if it's a known framework
            if pkg in FRAMEWORK_TAGS:
                frameworks.append(pkg)

    return deps, frameworks


def parse_package_json(content: str) -> Tuple[Dict[str, str], Dict[str, str], List[str]]:
    """
    Parse a package.json file content.
    Returns (deps, dev_deps, detected_frameworks).
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {}, {}, []

    deps = data.get("dependencies", {})
    dev_deps = data.get("devDependencies", {})
    frameworks = []

    for pkg in {**deps, **dev_deps}:
        pkg_lower = pkg.lower()
        if pkg_lower in FRAMEWORK_TAGS:
            frameworks.append(pkg_lower)

    return deps, dev_deps, frameworks


def parse_pyproject_toml(content: str) -> Tuple[Dict[str, str], List[str]]:
    """
    Parse a pyproject.toml file content (basic parser, no toml dependency).
    Extracts from [project.dependencies] and [project.optional-dependencies].
    """
    deps = {}
    frameworks = []
    in_deps_section = False

    for line in content.splitlines():
        stripped = line.strip()

        # Detect [project] dependencies section
        if stripped == "dependencies = [":
            in_deps_section = True
            continue

        if in_deps_section:
            if stripped == "]":
                in_deps_section = False
                continue

            # Parse "package>=version",
            match = re.match(r'"([a-zA-Z0-9_.-]+)\s*([><=!~]+[\d.*]+)?.*"', stripped)
            if match:
                pkg = match.group(1).lower()
                version = match.group(2) or "*"
                deps[pkg] = version

                if pkg in FRAMEWORK_TAGS:
                    frameworks.append(pkg)

    return deps, frameworks


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Context Builder
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CodebaseContextBuilder:
    """
    Scans a project directory and builds a ProjectContext.

    Looks for:
    - requirements.txt (Python)
    - package.json (Node.js)
    - pyproject.toml (Python modern)
    """

    SCANNABLE_FILES = {
        "requirements.txt": "python",
        "package.json": "javascript",
        "pyproject.toml": "python",
    }

    def build(self, project_path: str) -> ProjectContext:
        """
        Scan a project directory and build its context.
        """
        project_path = Path(project_path)
        project_name = project_path.name

        all_deps = {}
        all_dev_deps = {}
        languages = set()
        frameworks = set()
        ecosystems = set()

        for filename, lang in self.SCANNABLE_FILES.items():
            filepath = project_path / filename
            if not filepath.exists():
                continue

            try:
                content = filepath.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                logger.warning(f"Failed to read {filepath}: {e}")
                continue

            if filename == "requirements.txt":
                deps, fw = parse_requirements_txt(content)
                all_deps.update(deps)
                frameworks.update(fw)
                languages.add("python")
                ecosystems.add("pypi")

            elif filename == "package.json":
                deps, dev_deps, fw = parse_package_json(content)
                all_deps.update(deps)
                all_dev_deps.update(dev_deps)
                frameworks.update(fw)
                languages.add("javascript")
                ecosystems.add("npm")

            elif filename == "pyproject.toml":
                deps, fw = parse_pyproject_toml(content)
                all_deps.update(deps)
                frameworks.update(fw)
                languages.add("python")
                ecosystems.add("pypi")

        # Auto-generate tech tags from detected frameworks
        tech_tags = set()
        for fw in frameworks:
            tech_tags.update(FRAMEWORK_TAGS.get(fw, []))

        context = ProjectContext(
            project_name=project_name,
            direct_deps=all_deps,
            dev_deps=all_dev_deps,
            languages=sorted(languages),
            frameworks=sorted(frameworks),
            ecosystems=sorted(ecosystems),
            tech_tags=sorted(tech_tags),
        )

        logger.info(
            f"Built context for '{project_name}': "
            f"{len(all_deps)} deps, {len(frameworks)} frameworks, "
            f"tags={context.tech_tags}"
        )

        return context


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Signal Relevance Scorer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def score_signal_relevance(signal_title: str, signal_content: str,
                           signal_metadata: Dict, context: ProjectContext) -> float:
    """
    Score a signal's relevance to the user's codebase (0.0 → 1.0).

    Scoring criteria:
    - Direct dependency mention: +0.4
    - Framework match: +0.2
    - Tech tag overlap: +0.15 per tag (max 0.3)
    - Language ecosystem match: +0.1
    - CVE/security + dep match: +0.5 (critical boost)
    """
    score = 0.0
    text_lower = f"{signal_title} {signal_content}".lower()

    # 1. Direct dependency mentions
    dep_matches = 0
    for dep in context.dep_names:
        if dep in text_lower:
            dep_matches += 1

    if dep_matches > 0:
        score += min(0.4, dep_matches * 0.15)

    # 2. Framework match
    for fw in context.frameworks:
        if fw in text_lower:
            score += 0.2
            break

    # 3. Tech tag overlap
    signal_tags = set(signal_metadata.get("tags", []))
    if isinstance(signal_tags, list):
        signal_tags = {t.lower() for t in signal_tags}

    tag_overlap = signal_tags & set(context.tech_tags)
    score += min(0.3, len(tag_overlap) * 0.15)

    # 4. Language/ecosystem match
    signal_lang = signal_metadata.get("language", "").lower()
    if signal_lang in [l.lower() for l in context.languages]:
        score += 0.1

    # 5. CVE/security critical boost
    security_keywords = {"cve", "vulnerability", "security", "exploit", "patch", "advisory"}
    if any(kw in text_lower for kw in security_keywords):
        # If it mentions a dep we use, it's critical
        if dep_matches > 0:
            score += 0.5

    return min(1.0, score)
