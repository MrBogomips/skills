#!/usr/bin/env python3
"""Final validation of a plugin: manifest, skill and agent frontmatter, the authoring rulebook, READMEs.

Usage: validate.py [--json] [--no-claude] [--portable] [--custom] <plugin-root>

--portable: the plugin's skills are also distributed through the `skills` CLI (stricter frontmatter keys).
--custom: the skills are project- or user-scoped, not published (no English check).

Runs `claude plugin validate <root> --strict` too when the `claude` CLI is on
PATH (skip it with --no-claude). Exit status: 0 no errors, 1 errors, 2 bad usage.
The rules come from the official documentation listed in
shared/official-references.md and from the README contract.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import inventory  # noqa: E402
import mdparse  # noqa: E402
import readme_lint  # noqa: E402
import skill_lint  # noqa: E402
from readme_lint import Finding, finding  # noqa: E402

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$")
CLAUDE_TIMEOUT_SECONDS = 180


def _check_manifest(root: str, plugin: Dict[str, Any]) -> List[Finding]:
    path = os.path.join(root, plugin["manifest"])
    found = []
    name, version, description = plugin["name"], plugin["version"], plugin["description"]
    if not isinstance(name, str) or not KEBAB.match(name):
        found.append(finding("error", path, 1, "name", "must be lowercase words joined by hyphens"))
    if not isinstance(version, str) or not SEMVER.match(version):
        found.append(finding("error", path, 1, "version", "must be a semantic version such as 1.2.3"))
    if not isinstance(description, str) or not description.strip():
        found.append(finding("error", path, 1, "description", "is missing or empty"))
    return found


def _read_frontmatter(path: str) -> Optional[Dict[str, str]]:
    try:
        with open(path, encoding="utf-8") as handle:
            return mdparse.split_frontmatter(handle.read())[0]
    except (OSError, UnicodeDecodeError):
        return None


def _check_skill(root: str, skill: Dict[str, Any]) -> List[Finding]:
    return skill_lint.check_frontmatter(os.path.join(root, skill["directory"]))


def _check_agent(root: str, agent: Dict[str, str]) -> List[Finding]:
    path = os.path.join(root, agent["file"])
    front = _read_frontmatter(path)
    if front is None:
        return [finding("error", path, 1, "frontmatter", "missing or unreadable frontmatter")]
    return [finding("error", path, 1, key, "is missing or empty")
            for key in ("name", "description") if not front.get(key, "").strip()]


def _check_readmes(root: str, inv: Dict[str, Any]) -> List[Finding]:
    found = []
    targets = [(inv["plugin"], "plugin")] + [(skill, "skill") for skill in inv["skills"]]
    for component, profile in targets:
        path = os.path.join(root, component["readme"])
        if not component["readme_exists"]:
            found.append(finding("error", path, 1, "file", "README.md is missing for %s" % component["name"]))
            continue
        found += readme_lint.lint_file(path, profile, inv if profile == "plugin" else None)
    return found


def _run_claude(root: str) -> List[Finding]:
    command = shutil.which("claude")
    if not command:
        return [finding("info", root, 1, "claude plugin validate", "`claude` not found on PATH; skipped")]
    try:
        done = subprocess.run([command, "plugin", "validate", root, "--strict"], capture_output=True,
                              encoding="utf-8", errors="replace", timeout=CLAUDE_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as error:
        return [finding("warning", root, 1, "claude plugin validate", "could not run: %s" % error)]
    if done.returncode == 0:
        return [finding("info", root, 1, "claude plugin validate", "passed with --strict")]
    tail = " | ".join((done.stdout + done.stderr).strip().splitlines()[-8:])
    return [finding("error", root, 1, "claude plugin validate", "failed with --strict: %s" % tail)]


def validate(root: str, run_claude: bool = True, portable: bool = False, public: bool = True) -> List[Finding]:
    """Return every finding for the plugin rooted at `root`."""
    try:
        inv = inventory.build_inventory(root)
    except inventory.InventoryError as error:
        return [finding("error", root, 1, "manifest", str(error))]
    found = _check_manifest(root, inv["plugin"])
    for skill in inv["skills"]:
        found += _check_skill(root, skill)
        found += skill_lint.lint_skill(os.path.join(root, skill["directory"]), portable, public)
    for agent in inv["agents"]:
        found += _check_agent(root, agent)
        found += skill_lint.lint_agent(os.path.join(root, agent["file"]), public)
    found += _check_readmes(root, inv)
    if run_claude:
        found += _run_claude(root)
    return found


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Final validation of a Claude Code plugin.")
    parser.add_argument("--json", action="store_true", help="print the findings as JSON")
    parser.add_argument("--no-claude", action="store_true", help="skip `claude plugin validate --strict`")
    parser.add_argument("--portable", action="store_true",
                        help="the skills are also distributed through the skills CLI")
    parser.add_argument("--custom", action="store_true", help="unpublished skills: skip the English check")
    parser.add_argument("root")
    args = parser.parse_args(argv)
    findings = validate(args.root, run_claude=not args.no_claude, portable=args.portable, public=not args.custom)
    sys.stdout.write(readme_lint.format_findings(findings, args.json) + "\n")
    return 1 if readme_lint.has_errors(findings) else 0


if __name__ == "__main__":
    sys.exit(main())
