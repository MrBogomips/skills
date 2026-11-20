#!/usr/bin/env python3
"""List the components a Claude Code plugin distributes, as JSON.

Usage: inventory.py <plugin-root>

The plugin manifest and the real folder structure decide what is distributed.
SKILL.md files found elsewhere under the root (internal skills, fixtures, other
plugins) are reported under "excluded" with the reason.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mdparse  # noqa: E402

MANIFEST = os.path.join(".claude-plugin", "plugin.json")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
INTERNAL_DIRS = (os.path.join(".claude", "skills"), os.path.join(".agents", "skills"),
                 os.path.join(".codex", "skills"))
FIXTURE_PARTS = {"tests", "test", "evals", "fixtures", "examples"}


class InventoryError(Exception):
    """The plugin root or its manifest cannot be read."""


def read_manifest(root: str) -> Dict[str, Any]:
    path = os.path.join(root, MANIFEST)
    try:
        with open(path, encoding="utf-8") as handle:
            manifest = json.load(handle)
    except OSError as error:
        raise InventoryError("cannot read %s: %s" % (path, error.strerror or error))
    except ValueError as error:
        raise InventoryError("%s is not valid JSON: %s" % (path, error))
    if not isinstance(manifest, dict):
        raise InventoryError("%s must contain a JSON object" % path)
    return manifest


def _frontmatter(path: str) -> Optional[Dict[str, str]]:
    try:
        with open(path, encoding="utf-8") as handle:
            return mdparse.split_frontmatter(handle.read())[0]
    except (OSError, UnicodeDecodeError):
        return None


def _rel(root: str, path: str) -> str:
    return os.path.relpath(path, root).replace(os.sep, "/")


def _as_paths(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _skill_dirs(root: str, manifest: Dict[str, Any]) -> List[str]:
    """Skill folders: skills/* plus the paths the manifest's `skills` field adds."""
    found = []  # type: List[str]
    for base in ["skills"] + _as_paths(manifest.get("skills")):
        base_dir = os.path.normpath(os.path.join(root, base))
        if os.path.isfile(os.path.join(base_dir, "SKILL.md")):
            candidates = [base_dir]
        elif os.path.isdir(base_dir):
            candidates = [os.path.join(base_dir, name) for name in sorted(os.listdir(base_dir))]
        else:
            candidates = []
        found += [path for path in candidates
                  if os.path.isfile(os.path.join(path, "SKILL.md")) and path not in found]
    return found


def _skill_entry(root: str, skill_dir: str) -> Dict[str, Any]:
    front = _frontmatter(os.path.join(skill_dir, "SKILL.md")) or {}
    readme = os.path.join(skill_dir, "README.md")
    return {
        "name": front.get("name") or os.path.basename(skill_dir),
        "directory": _rel(root, skill_dir),
        "skill_file": _rel(root, os.path.join(skill_dir, "SKILL.md")),
        "readme": _rel(root, readme),
        "readme_exists": os.path.isfile(readme),
    }


def _markdown_components(root: str, manifest: Dict[str, Any], key: str, nested_file: str) -> List[Dict[str, str]]:
    """Agents or commands: <key>/**/*.md, or the paths the manifest declares instead.

    An agent needs frontmatter, so other Markdown files in an agents folder are not agents.
    """
    entries = []
    for base in (_as_paths(manifest[key]) if manifest.get(key) is not None else [key]):
        base_dir = os.path.normpath(os.path.join(root, base))
        if os.path.isfile(base_dir):
            files = [base_dir]
        else:
            files = [os.path.join(folder, name)
                     for folder, _, names in os.walk(base_dir)
                     for name in names if name.endswith(".md") and name.lower() != "readme.md"]
        for path in sorted(files):
            stem = os.path.splitext(os.path.basename(path))[0]
            fallback = os.path.basename(os.path.dirname(path)) if stem == nested_file else stem
            front = _frontmatter(path)
            if front is None and key == "agents":
                continue
            front = front or {}
            entries.append({"name": front.get("name") or fallback, "file": _rel(root, path)})
    return entries


def _hook_events(source: Any, origin: str) -> List[Dict[str, str]]:
    events = source.get("hooks", source) if isinstance(source, dict) else None
    if not isinstance(events, dict):
        return [{"event": "unreadable", "file": origin}]
    return [{"event": event, "file": origin} for event in sorted(events)]


def _hooks(root: str, manifest: Dict[str, Any]) -> List[Dict[str, str]]:
    """Hook events of hooks/hooks.json merged with the ones the manifest declares."""
    declared = manifest.get("hooks")
    files = [os.path.join("hooks", "hooks.json")] if os.path.isfile(os.path.join(root, "hooks", "hooks.json")) else []
    files += [path for path in _as_paths(declared) if os.path.normpath(path) not in map(os.path.normpath, files)]
    found = []  # type: List[Dict[str, str]]
    for relative in files:
        path = os.path.normpath(os.path.join(root, relative))
        try:
            with open(path, encoding="utf-8") as handle:
                found += _hook_events(json.load(handle), _rel(root, path))
        except (OSError, ValueError):
            found.append({"event": "unreadable", "file": _rel(root, path)})
    if isinstance(declared, dict):
        found += _hook_events(declared, MANIFEST.replace(os.sep, "/"))
    return found


def _exclusion_reason(root: str, skill_dir: str) -> str:
    relative = _rel(root, skill_dir)
    if any(relative.startswith(prefix.replace(os.sep, "/") + "/") for prefix in INTERNAL_DIRS):
        return "internal skill of the repository"
    if FIXTURE_PARTS.intersection(relative.split("/")):
        return "test fixture or example"
    current = os.path.dirname(skill_dir)
    while os.path.abspath(current) != os.path.abspath(root) and len(current) > len(root):
        if os.path.isfile(os.path.join(current, MANIFEST)):
            return "belongs to the plugin in %s" % _rel(root, current)
        current = os.path.dirname(current)
    return "outside the plugin's skill folders"


def _excluded(root: str, distributed: List[str]) -> List[Dict[str, str]]:
    kept = {os.path.abspath(path) for path in distributed}
    excluded = []
    for folder, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        if "SKILL.md" in names and os.path.abspath(folder) not in kept:
            excluded.append({"skill_file": _rel(root, os.path.join(folder, "SKILL.md")),
                             "reason": _exclusion_reason(root, folder)})
    return excluded


def _plugin_readme(root: str) -> str:
    """`README.md`, or `skills/README.md` when the root also hosts other plugins.

    In such a repository the root README is the page of the repository, so the
    README of the root plugin sits with its skills.
    """
    for name in sorted(os.listdir(root)):
        if os.path.isfile(os.path.join(root, name, MANIFEST)):
            return "skills/README.md"
    return "README.md"


def build_inventory(root: str) -> Dict[str, Any]:
    """Return the inventory of the plugin rooted at `root`."""
    if not os.path.isdir(root):
        raise InventoryError("%s is not a directory" % root)
    manifest = read_manifest(root)
    skill_dirs = _skill_dirs(root, manifest)
    readme_path = _plugin_readme(root)
    readme = os.path.join(root, readme_path)
    return {
        "root": os.path.abspath(root),
        "plugin": {
            "name": manifest.get("name"),
            "version": manifest.get("version"),
            "description": manifest.get("description"),
            "license": manifest.get("license"),
            "manifest": MANIFEST.replace(os.sep, "/"),
            "readme": readme_path,
            "readme_exists": os.path.isfile(readme),
        },
        "skills": [_skill_entry(root, path) for path in skill_dirs],
        "agents": _markdown_components(root, manifest, "agents", "AGENT"),
        "commands": _markdown_components(root, manifest, "commands", "COMMAND"),
        "hooks": _hooks(root, manifest),
        "excluded": _excluded(root, skill_dirs),
    }


def main(argv: List[str]) -> int:
    if len(argv) != 2 or argv[1] in ("-h", "--help"):
        sys.stderr.write(__doc__)
        return 2
    try:
        inventory = build_inventory(argv[1])
    except InventoryError as error:
        sys.stderr.write("inventory: %s\n" % error)
        return 2
    json.dump(inventory, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
