#!/usr/bin/env python3
"""Check the structure of a public README against the skill-maker contract.

Usage: readme_lint.py --profile plugin|skill [--plugin-root DIR] [--base-dir DIR] [--json] README...

--plugin-root (plugin profile) also checks the README against the components
the plugin really distributes. --base-dir is the folder a draft is meant for:
its relative links resolve from there instead of from the draft's own folder. Exit status: 0 no errors, 1 errors, 2 bad usage.
The contract itself is described in skills/skill-readme/references/contract.md.
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import inventory as inventory_module  # noqa: E402
import mdparse  # noqa: E402

Finding = Dict[str, Any]

# (title, required) in contract order; "last" is a required closing section.
PROFILES = {
    "plugin": {
        "sections": [("Why", True), ("Use cases", False), ("Included components", True),
                     ("Agents", False), ("Commands", False), ("Hooks", False),
                     ("Installation", True), ("Quick start", True), ("Requirements", False),
                     ("Configuration", False), ("Limitations", False)],
        "last": "License",
    },
    "skill": {
        "sections": [("Why", True), ("Use cases", False), ("Installation", False), ("Usage", True),
                     ("Inputs and outputs", False), ("Requirements", False), ("Limitations", False)],
        "last": None,
    },
}
ALIASES = {"install": "Installation", "licence": "License", "gettingstarted": "Quick start",
           "usecase": "Use cases", "inputsoutputs": "Inputs and outputs"}
SCENARIO_LABELS = ("**Context:**", "**Action:**", "**Result:**")
MAX_SUMMARY = 200
# Word budgets of the text a README adds to the sources; fenced blocks and custom sections do not count.
MAX_INTRO_WORDS = 60
MAX_SECTION_WORDS = 150
SECTION_WORDS = {"Why": 120, "Use cases": 240}
MAX_COMPONENT_WORDS = 40
MAX_SKILL_WORDS = 30
MAX_SCENARIOS = 3
COMPONENT_SECTIONS = (("Agents", "agents"), ("Commands", "commands"), ("Hooks", "hooks"))
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_SQUASH = re.compile(r"[^a-z0-9]")


def finding(severity: str, path: str, line: int, section: str, message: str) -> Finding:
    return {"severity": severity, "path": path, "line": line, "section": section, "message": message}


def _contract_titles(profile: str) -> List[str]:
    spec = PROFILES[profile]
    return [title for title, _ in spec["sections"]] + ([spec["last"]] if spec["last"] else [])


def _canonical(title: str, profile: str) -> Optional[str]:
    """The contract title this heading stands for, exact or misspelled; else None."""
    titles = _contract_titles(profile)
    if title in titles:
        return title
    squashed = _SQUASH.sub("", title.casefold())
    for candidate in titles:
        if _SQUASH.sub("", candidate.casefold()) == squashed:
            return candidate
    alias = ALIASES.get(squashed)
    return alias if alias in titles else None


def _check_head(doc: Dict[str, Any], path: str) -> List[Finding]:
    found = []
    front = doc["frontmatter"]
    if front is None:
        found.append(finding("error", path, 1, "frontmatter", "missing YAML frontmatter with `summary:`"))
    elif not front.get("summary", "").strip():
        found.append(finding("error", path, 1, "frontmatter", "`summary:` is missing or empty"))
    elif len(front["summary"]) > MAX_SUMMARY:
        found.append(finding("warning", path, 1, "frontmatter", "`summary:` has %d characters; keep it within %d"
                             % (len(front["summary"]), MAX_SUMMARY)))
    h1s = doc["h1"]
    if not h1s:
        return found + [finding("error", path, 1, "H1", "no H1 title")]
    if len(h1s) > 1:
        found.append(finding("error", path, h1s[1]["line"], "H1", "more than one H1; keep a single title"))
    if doc["headings"][0]["level"] != 1:
        found.append(finding("error", path, doc["headings"][0]["line"], "H1", "the H1 must be the first heading"))
    if not doc["intro"]:
        found.append(finding("error", path, h1s[0]["line"], "introduction",
                             "no introductory paragraph between the H1 and the first section"))
    elif len(doc["intro"].split()) > MAX_INTRO_WORDS:
        found.append(finding("warning", path, h1s[0]["line"], "introduction",
                             "%d words; keep the first paragraph within %d"
                             % (len(doc["intro"].split()), MAX_INTRO_WORDS)))
    return found


def _check_titles(sections: List[Dict[str, Any]], profile: str, path: str) -> List[Finding]:
    """Exact titles and no duplicates. Sets section["contract"] as a side product."""
    found = []
    seen = {}  # type: Dict[str, int]
    for section in sections:
        section["contract"] = _canonical(section["title"], profile)
        key = section["contract"] or section["title"]
        if section["contract"] and section["contract"] != section["title"]:
            found.append(finding("error", path, section["line"], section["title"],
                                 "title must be exactly `%s`" % section["contract"]))
        if key in seen:
            found.append(finding("error", path, section["line"], section["title"],
                                 "duplicate H2; first at line %d" % seen[key]))
        seen.setdefault(key, section["line"])
    return found


def _check_order(sections: List[Dict[str, Any]], profile: str, path: str) -> List[Finding]:
    spec = PROFILES[profile]
    order = [title for title, _ in spec["sections"]]
    present = {s["contract"] for s in sections if s["contract"]}
    found = [finding("error", path, 1, title, "required section is missing")
             for title, required in spec["sections"] + ([(spec["last"], True)] if spec["last"] else [])
             if required and title not in present]
    core = [s for s in sections if s["contract"] in order]
    highest = -1
    for section in core:
        index = order.index(section["contract"])
        if index < highest:
            found.append(finding("error", path, section["line"], section["title"],
                                 "out of order; contract order is %s" % ", ".join(order)))
        highest = max(highest, index)
    last_core_line = max([s["line"] for s in core] or [0])
    for section in sections:
        if section["contract"]:
            continue
        if section["line"] < last_core_line:
            found.append(finding("error", path, section["line"], section["title"],
                                 "custom section must come after the contract sections"))
        else:
            found.append(finding("info", path, section["line"], section["title"],
                                 "custom section: kept, ignored by extraction"))
    if spec["last"] and sections and spec["last"] in present and sections[-1]["contract"] != spec["last"]:
        found.append(finding("error", path, sections[-1]["line"], spec["last"],
                             "`%s` must be the last section" % spec["last"]))
    return found


def _words(body: List[str]) -> int:
    """Words of a section body outside fenced code blocks."""
    count, fenced = 0, False
    for line in body:
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced:
            count += len(line.split())
    return count


def _word_limit(title: str, inv: Optional[Dict[str, Any]]) -> int:
    for component_title, key in COMPONENT_SECTIONS:
        if title == component_title:
            return MAX_COMPONENT_WORDS * max(1, len(inv[key]) if inv else 1)
    if title == "Included components" and inv:
        return MAX_SKILL_WORDS * max(1, len(inv["skills"]))
    return SECTION_WORDS.get(title, MAX_SECTION_WORDS)


def _check_bodies(sections: List[Dict[str, Any]], lines: List[str], path: str,
                  inv: Optional[Dict[str, Any]] = None) -> List[Finding]:
    found = []
    for section in sections:
        body = lines[section["line"]: section["end"] - 1]
        if not any(line.strip() for line in body):
            found.append(finding("error", path, section["line"], section["title"], "section is empty"))
        if section["contract"]:
            words, limit = _words(body), _word_limit(section["contract"], inv)
            if words > limit:
                found.append(finding("warning", path, section["line"], section["title"],
                                     "%d words; keep it within %d and leave the detail to the sources"
                                     % (words, limit)))
        if section["contract"] == "Use cases":
            found += _check_scenarios(section, lines, path)
    return found


def _check_scenarios(section: Dict[str, Any], lines: List[str], path: str) -> List[Finding]:
    if not section["h3"]:
        return [finding("error", path, section["line"], section["title"], "needs at least one scenario as an H3")]
    found = []
    if len(section["h3"]) > MAX_SCENARIOS:
        found.append(finding("warning", path, section["line"], section["title"],
                             "%d scenarios; keep at most %d" % (len(section["h3"]), MAX_SCENARIOS)))
    ends = [head["line"] for head in section["h3"][1:]] + [section["end"]]
    for head, end in zip(section["h3"], ends):
        body = "\n".join(lines[head["line"]: end - 1])
        missing = [label for label in SCENARIO_LABELS if label not in body]
        if missing:
            found.append(finding("warning", path, head["line"], section["title"],
                                 "scenario `%s` lacks %s" % (head["title"], ", ".join(missing))))
    return found


def _section_at(sections: List[Dict[str, Any]], line: int) -> str:
    for section in sections:
        if section["line"] <= line < section["end"]:
            return section["title"]
    return "introduction"


def _local_target(target: str) -> Optional[str]:
    """The file part of a relative link, or None for URLs, anchors and absolute paths."""
    if _SCHEME.match(target) or target.startswith(("#", "/")):
        return None
    return unquote(target.split("#", 1)[0].split("?", 1)[0]) or None


def _slug(title: str) -> str:
    """GitHub-style anchor of a heading."""
    text = re.sub(r"[^\w\- ]", "", title.strip().lower().replace("`", ""))
    return text.replace(" ", "-")


def _anchors(target_path: str, own: Dict[str, Any], same: bool) -> Optional[set]:
    if same:
        return {_slug(h["title"]) for h in own["headings"]}
    if not target_path.lower().endswith(".md"):
        return None
    try:
        with open(target_path, encoding="utf-8") as handle:
            return {_slug(h["title"]) for h in mdparse.parse(handle.read())["headings"]}
    except (OSError, UnicodeDecodeError):
        return None


def _check_links(doc: Dict[str, Any], path: str, base_dir: Optional[str]) -> List[Finding]:
    found = []
    base = base_dir or os.path.dirname(os.path.abspath(path))
    for link in doc["links"]:
        target = link["target"]
        section = _section_at(doc["sections"], link["line"])
        local = _local_target(target)
        if local and not os.path.exists(os.path.join(base, local)):
            found.append(finding("error", path, link["line"], section,
                                 "relative link target does not exist: %s" % target))
            continue
        if "#" not in target or _SCHEME.match(target) or target.startswith("/"):
            continue
        fragment = unquote(target.split("#", 1)[1])
        anchors = _anchors(os.path.join(base, local) if local else "", doc, not local)
        if anchors is not None and fragment and fragment not in anchors:
            found.append(finding("error", path, link["line"], section,
                                 "no heading for the anchor in: %s" % target))
    return found


def _check_components(doc: Dict[str, Any], lines: List[str], path: str, inv: Dict[str, Any]) -> List[Finding]:
    found = []
    by_title = {s["contract"]: s for s in doc["sections"] if s["contract"]}
    for title, key in COMPONENT_SECTIONS:
        if inv[key] and title not in by_title:
            found.append(finding("error", path, 1, title,
                                 "the plugin ships %s (%s) but the section is missing"
                                 % (key, ", ".join(sorted({str(c.get("name") or c.get("event")) for c in inv[key]})))))
        elif title in by_title and not inv[key]:
            found.append(finding("warning", path, by_title[title]["line"], title,
                                 "section present but the plugin ships no %s" % key))
    included = by_title.get("Included components")
    if not included:
        return found
    text = "\n".join(lines[included["line"]: included["end"] - 1])
    here = os.path.dirname(inv.get("plugin", {}).get("readme", ""))
    targets = {os.path.join(here, t) for t in
               (_local_target(l["target"]) for l in doc["links"] if included["line"] <= l["line"] < included["end"])
               if t}
    for skill in inv["skills"]:
        if not re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(skill["name"]), text):
            found.append(finding("error", path, included["line"], "Included components",
                                 "distributed skill not listed: %s" % skill["name"]))
        elif skill["readme_exists"] and skill["readme"] not in {os.path.normpath(t).replace(os.sep, "/")
                                                                 for t in targets if t}:
            found.append(finding("warning", path, included["line"], "Included components",
                                 "no link to %s" % skill["readme"]))
    return found


def lint_text(text: str, profile: str, path: str, inv: Optional[Dict[str, Any]] = None,
              base_dir: Optional[str] = None) -> List[Finding]:
    """Return the findings for one README. `inv` is an inventory.build_inventory result.

    Relative links resolve from `base_dir`, by default the folder of `path`: pass the
    folder the README is meant for when checking a draft kept elsewhere.
    """
    if profile not in PROFILES:
        raise ValueError("unknown profile: %s" % profile)
    doc = mdparse.parse(text)
    lines = text.splitlines()
    found = _check_head(doc, path)
    found += _check_titles(doc["sections"], profile, path)
    found += _check_order(doc["sections"], profile, path)
    found += _check_bodies(doc["sections"], lines, path, inv)
    found += _check_links(doc, path, base_dir)
    if profile == "plugin" and inv is not None:
        found += _check_components(doc, lines, path, inv)
    return sorted(found, key=lambda f: (f["path"], f["line"]))


def lint_file(path: str, profile: str, inv: Optional[Dict[str, Any]] = None,
              base_dir: Optional[str] = None) -> List[Finding]:
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as error:
        return [finding("error", path, 1, "file", "cannot read: %s" % error)]
    return lint_text(text, profile, path, inv, base_dir)


def has_errors(findings: List[Finding]) -> bool:
    return any(f["severity"] == "error" for f in findings)


def format_findings(findings: List[Finding], as_json: bool = False) -> str:
    if as_json:
        return json.dumps(findings, indent=2)
    rows = ["%-7s %s:%d  [%s]  %s" % (f["severity"], f["path"], f["line"], f["section"], f["message"])
            for f in findings]
    counts = {level: sum(1 for f in findings if f["severity"] == level) for level in ("error", "warning", "info")}
    rows.append("%d error(s), %d warning(s), %d note(s)" % (counts["error"], counts["warning"], counts["info"]))
    return "\n".join(rows)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check a README against the skill-maker contract.")
    parser.add_argument("--profile", required=True, choices=sorted(PROFILES))
    parser.add_argument("--plugin-root", help="plugin folder, to check the README against its components")
    parser.add_argument("--base-dir", help="folder a draft is meant for; relative links resolve from it")
    parser.add_argument("--json", action="store_true", help="print the findings as JSON")
    parser.add_argument("readme", nargs="+")
    args = parser.parse_args(argv)
    inv = None
    if args.plugin_root:
        try:
            inv = inventory_module.build_inventory(args.plugin_root)
        except inventory_module.InventoryError as error:
            sys.stderr.write("readme_lint: %s\n" % error)
            return 2
    findings = []  # type: List[Finding]
    for path in args.readme:
        findings += lint_file(path, args.profile, inv, args.base_dir)
    sys.stdout.write(format_findings(findings, args.json) + "\n")
    return 1 if has_errors(findings) else 0


if __name__ == "__main__":
    sys.exit(main())
