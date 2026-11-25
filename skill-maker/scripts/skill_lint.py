#!/usr/bin/env python3
"""Mechanical checks of a skill directory and of an agent file against the authoring rulebook.

Usage: skill_lint.py [--json] [--portable] [--custom] <skill-dir>...

For a skill outside any plugin; validate.py calls lint_skill and lint_agent for a whole plugin.
Rule IDs refer to shared/rules/. Standard library only. Exit status: 0 no errors, 1 errors, 2 bad usage.
"""

import argparse
import os
import re
import sys
from typing import Dict, FrozenSet, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lang_heuristic  # noqa: E402
import mdparse  # noqa: E402
import readme_lint  # noqa: E402
from readme_lint import Finding, finding  # noqa: E402

PORTABLE_KEYS: FrozenSet[str] = frozenset(
    ["name", "description", "license", "compatibility", "metadata", "allowed-tools"])
CLAUDE_CODE_KEYS: FrozenSet[str] = frozenset(
    ["when_to_use", "argument-hint", "arguments", "disable-model-invocation", "user-invocable",
     "disallowed-tools", "model", "effort", "context", "agent", "background", "hooks", "paths", "shell"])
MAX_SKILL_LINES = 500
MAX_NAME = 64
MAX_DESCRIPTION = 1024
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DEV_DIRS = frozenset(["tests", "evals", "scenarios"])
IGNORED_DIRS = frozenset(["__pycache__", ".git"])
SCRIPT_EXTENSIONS = (".py", ".sh", ".js", ".mjs", ".rb", ".pl")
RUN_VERBS = r"(?:run|re-run|rerun|execute|call|invoke)"
_PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|FIXME)\b|\{\{[^}]*\}\}|<(?:placeholder|insert[^>]*)>")
_INLINE_CODE = re.compile(r"`+[^`]*`+")
_KEY_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.-]*):")


def _read(path: str) -> Optional[str]:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError):
        return None


def _key_lines(text: str) -> Dict[str, int]:
    """Line number of each top-level frontmatter key (none when the file has no frontmatter)."""
    found: Dict[str, int] = {}
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return found
    for number, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            break
        match = _KEY_LINE.match(line)
        if match:
            found[match.group(1)] = number
    return found


def _check_keys(path: str, text: str, portable: bool) -> List[Finding]:
    found = []
    for key, line in _key_lines(text).items():
        if key in PORTABLE_KEYS:
            continue
        if key in CLAUDE_CODE_KEYS:
            if portable:
                found.append(finding("info", path, line, "S12",
                                     "`%s` is Claude Code only: the skill must still work without it" % key))
            continue
        found.append(finding("error" if portable else "warning", path, line, "S12",
                             "`%s` is not a known frontmatter key" % key))
    return found


def _dev_files(skill_dir: str) -> List[Finding]:
    found = []
    for current, dirs, files in os.walk(skill_dir):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
        for name in list(dirs):
            if name in DEV_DIRS or name.endswith("-workspace"):
                found.append(finding("error", os.path.join(current, name), 1, "P6",
                                     "development folder inside the skill: it ships with the skill"))
                dirs.remove(name)
        for name in sorted(files):
            if name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py")):
                found.append(finding("error", os.path.join(current, name), 1, "P6",
                                     "test file inside the skill: it ships with the skill"))
    return found


def _bundled_scripts(skill_dir: str) -> List[str]:
    scripts = []
    for current, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for name in files:
            if name.endswith(SCRIPT_EXTENSIONS):
                scripts.append(os.path.relpath(os.path.join(current, name), skill_dir).replace(os.sep, "/"))
    return scripts


def _script_patterns(scripts: List[str]) -> List[Tuple[str, "re.Pattern[str]", "re.Pattern[str]"]]:
    prefix = r"(?:\./|<[^>]+>/|\$\{?\w+\}?/|\"\$\{?\w+\}?/)?"
    return [(rel,
             re.compile(r"^\s*(?:\$\s+)?" + prefix + re.escape(rel) + r"(?![\w.])"),
             re.compile(r"\b" + RUN_VERBS + r"\s+`" + prefix + re.escape(rel) + r"(?![\w.])", re.IGNORECASE))
            for rel in scripts]


def _code_lines(lines: List[str]) -> List[Tuple[int, str]]:
    prose = {offset for offset, _ in mdparse.prose_lines(lines)}
    return [(offset, line) for offset, line in enumerate(lines)
            if offset not in prose and not line.lstrip().startswith(("```", "~~~"))]


def _check_markdown(path: str, text: str, patterns, public: bool) -> List[Finding]:
    front, body, start = mdparse.split_frontmatter(text)
    found = []
    prose = list(mdparse.prose_lines(body))
    for offset, line in _code_lines(body):
        for rel, at_start, _ in patterns:
            if at_start.search(line):
                found.append(finding("warning", path, start + offset, "S7",
                                     "`%s` is run without its interpreter (python3, bash...)" % rel))
    for offset, line in prose:
        for rel, _, after_verb in patterns:
            if after_verb.search(line):
                found.append(finding("warning", path, start + offset, "S7",
                                     "`%s` is run without its interpreter (python3, bash...)" % rel))
        if _PLACEHOLDER.search(_INLINE_CODE.sub(" ", line)):
            found.append(finding("warning", path, start + offset, "P3", "leftover placeholder"))
    if public:
        found += _check_language(path, text, front, prose, start)
    return found


def _check_language(path: str, text: str, front, prose, start: int) -> List[Finding]:
    found = []
    description = (front or {}).get("description", "")
    line = _key_lines(text).get("description", 1)
    for phrase in lang_heuristic.foreign_phrases(description):
        found.append(finding("warning", path, line, "S3", "trigger phrase not in English: \"%s\"" % phrase))
    for offset, prose_line in prose:
        for phrase in lang_heuristic.foreign_phrases(prose_line):
            found.append(finding("warning", path, start + offset, "S3", "phrase not in English: \"%s\"" % phrase))
    if lang_heuristic.looks_non_english(prose_line for _, prose_line in prose):
        found.append(finding("warning", path, start, "S3", "the text does not look like English"))
    return found


def check_frontmatter(skill_dir: str) -> List[Finding]:
    """Rule P1 and the description limits: `name` equals the directory, kebab-case, description present."""
    path = os.path.join(skill_dir, "SKILL.md")
    text = _read(path)
    front = mdparse.split_frontmatter(text)[0] if text is not None else None
    if front is None:
        return [finding("error", path, 1, "frontmatter", "missing or unreadable frontmatter")]
    found = []
    name, description = front.get("name", ""), front.get("description", "")
    directory = os.path.basename(os.path.normpath(skill_dir))
    if not name:
        found.append(finding("error", path, 1, "name", "is missing"))
    elif name != directory:
        found.append(finding("error", path, 1, "name", "`%s` differs from the directory `%s`" % (name, directory)))
    if name and (not KEBAB.match(name) or len(name) > MAX_NAME):
        found.append(finding("error", path, 1, "name",
                             "must be lowercase words joined by hyphens, at most %d characters" % MAX_NAME))
    if not description.strip():
        found.append(finding("error", path, 1, "description", "is missing or empty"))
    elif len(description) > MAX_DESCRIPTION:
        found.append(finding("error", path, 1, "description",
                             "has %d characters; the limit is %d" % (len(description), MAX_DESCRIPTION)))
    return found


def _markdown_files(skill_dir: str) -> List[str]:
    """The skill's README.md and every Markdown file under references/, nested folders included."""
    files = [os.path.join(skill_dir, "README.md")] if os.path.isfile(os.path.join(skill_dir, "README.md")) else []
    for current, dirs, names in os.walk(os.path.join(skill_dir, "references")):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
        files += [os.path.join(current, name) for name in sorted(names) if name.endswith(".md")]
    return files


def lint_skill(skill_dir: str, portable: bool, public: bool) -> List[Finding]:
    """Return the rulebook findings for the skill directory (its SKILL.md and references)."""
    skill_file = os.path.join(skill_dir, "SKILL.md")
    text = _read(skill_file)
    if text is None:
        return [finding("error", skill_file, 1, "P1", "SKILL.md is missing or unreadable")]
    found = _check_keys(skill_file, text, portable)
    if len(text.splitlines()) > MAX_SKILL_LINES:
        found.append(finding("warning", skill_file, MAX_SKILL_LINES + 1, "S4",
                             "SKILL.md is longer than %d lines: move detail to references" % MAX_SKILL_LINES))
    found += _dev_files(skill_dir)
    patterns = _script_patterns(_bundled_scripts(skill_dir))
    found += _check_markdown(skill_file, text, patterns, public)
    for path in _markdown_files(skill_dir):
        found += _check_markdown(path, _read(path) or "", patterns, public)
    return found


def lint_agent(agent_file: str, public: bool) -> List[Finding]:
    """Return the placeholder and language findings for an agent file."""
    return _check_markdown(agent_file, _read(agent_file) or "", [], public)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check skill directories against the authoring rulebook.")
    parser.add_argument("--json", action="store_true", help="print the findings as JSON")
    parser.add_argument("--portable", action="store_true",
                        help="the skills are also distributed through the skills CLI")
    parser.add_argument("--custom", action="store_true", help="unpublished skills: skip the English check")
    parser.add_argument("skill_dirs", nargs="+", metavar="skill-dir")
    args = parser.parse_args(argv)
    findings = []
    for skill_dir in args.skill_dirs:
        findings += check_frontmatter(skill_dir)
        findings += lint_skill(skill_dir, args.portable, not args.custom)
    sys.stdout.write(readme_lint.format_findings(findings, args.json) + "\n")
    return 1 if readme_lint.has_errors(findings) else 0


if __name__ == "__main__":
    sys.exit(main())
