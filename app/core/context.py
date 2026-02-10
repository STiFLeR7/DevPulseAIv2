import os
import json
import hashlib
from typing import Dict, List, Any

class ContextIngestor:
    """
    Parses project configuration files to build a context graph of the user's stack.
    """
    
    def ingest_directory(self, root_path: str) -> List[Dict[str, Any]]:
        """
        Scans a directory for known config files and parses them.
        """
        context_items = []
        
        # 1. Python: requirements.txt
        req_path = os.path.join(root_path, "requirements.txt")
        if os.path.exists(req_path):
            deps = self._parse_requirements(req_path)
            context_items.append({
                "source": "requirements.txt",
                "dependencies": deps,
                "tech_tags": ["python"] + list(deps.keys())
            })

        # 2. Node: package.json
        pkg_path = os.path.join(root_path, "package.json")
        if os.path.exists(pkg_path):
            deps = self._parse_package_json(pkg_path)
            context_items.append({
                "source": "package.json",
                "dependencies": deps,
                "tech_tags": ["javascript", "node"] + list(deps.keys())
            })
            
        # 3. Python: pyproject.toml (basic support)
        # TODO: Add robust TOML parsing
        
        return context_items

    def _parse_requirements(self, file_path: str) -> Dict[str, str]:
        dependencies = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    # Handle common operators: ==, >=, <=, >, <
                    # We can use regex but for now simple split is improved
                    import re
                    match = re.split(r'(==|>=|<=|>|<)', line)
                    if len(match) >= 3:
                        dependencies[match[0].strip()] = "".join(match[1:]).strip()
                    else:
                        dependencies[line.strip()] = "latest"
        except Exception as e:
            print(f"Error parsing requirements.txt: {e}")
        return dependencies

    def _parse_package_json(self, file_path: str) -> Dict[str, str]:
        dependencies = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                dependencies.update(deps)
                dependencies.update(dev_deps)
        except Exception as e:
            print(f"Error parsing package.json: {e}")
        return dependencies

    @staticmethod
    def generate_hash(content: Dict) -> str:
        serialized = json.dumps(content, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
