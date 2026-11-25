#!/usr/bin/env python3
"""Detect changes in the official plugins and documentation pages skill-maker's rulebook rests on.

Usage: official_drift.py [--baseline PATH] [--out FILE] [--refresh]

Compares skill-maker/shared/official-baseline.json with upstream: the last commit touching each plugin
folder (GitHub API) and the sha256 of each documentation page. On drift it writes an issue body to --out;
with no drift it writes nothing. --refresh records the current commits and hashes in the baseline instead.
Exit status: 0 done (drift or not), 1 a fetch failed (nothing written), 2 bad usage.
Standard library only. GITHUB_TOKEN, when set, is sent to api.github.com.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple

Fetch = Callable[[str], Tuple[int, bytes]]

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_BASELINE = os.path.join(ROOT, "skill-maker", "shared", "official-baseline.json")
RULES_DIR = os.path.join(ROOT, "skill-maker", "shared", "rules")
TIMEOUT_SECONDS = 30
_SOURCE = re.compile(r"^Official source:\s*(.+?)(?:\s*·.*)?$")
_RULE = re.compile(r"^###\s+([A-Z]\d+)\.")


class FetchError(Exception):
    pass


def http_fetch(url: str) -> Tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "official-drift-check"})
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        request.add_header("Authorization", "Bearer " + token)
        request.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, b""


def _get(url: str, fetch: Fetch) -> bytes:
    try:
        status, body = fetch(url)
    except (OSError, ValueError) as error:
        raise FetchError("%s: %s" % (url, error))
    if status != 200:
        raise FetchError("%s: HTTP %d" % (url, status))
    return body


def latest_commit(repo: str, path: str, fetch: Fetch) -> str:
    url = "https://api.github.com/repos/%s/commits?path=%s&per_page=1" % (repo, path)
    try:
        return json.loads(_get(url, fetch).decode("utf-8"))[0]["sha"]
    except (ValueError, KeyError, IndexError, TypeError) as error:
        raise FetchError("%s: unexpected answer (%s)" % (url, error))


def page_hash(url: str, fetch: Fetch) -> str:
    return hashlib.sha256(_get(url, fetch)).hexdigest()


def find_drift(baseline: Dict, fetch: Fetch) -> List[Dict]:
    drift = []
    for entry in baseline.get("plugins", []):
        new = latest_commit(entry["repo"], entry["path"], fetch)
        if new != entry["commit"]:
            drift.append({"key": entry["key"], "kind": "plugin", "old": entry["commit"], "new": new,
                          "link": "https://github.com/%s/compare/%s...%s" % (entry["repo"], entry["commit"], new),
                          "rules": entry["rules"]})
    for entry in baseline.get("pages", []):
        new = page_hash(entry["url"], fetch)
        if new != entry["sha256"]:
            drift.append({"key": entry["key"], "kind": "page", "old": entry["sha256"], "new": new,
                          "link": entry["url"], "rules": entry["rules"]})
    return drift


def issue_body(drift: List[Dict]) -> str:
    rows = ["| %s | %s | %s | %s |" % (d["key"], d["kind"], d["link"], ", ".join(d["rules"]) or "none")
            for d in drift]
    return "\n".join([
        "Official sources that skill-maker's rulebook rests on have changed since the baseline was recorded.",
        "",
        "| Source | Kind | What changed | Rules to re-check |",
        "|---|---|---|---|",
    ] + rows + [
        "",
        "Follow the **Official drift** procedure in `AGENTS.md`: re-check the listed rules with the",
        "`rulebook-reviewer` agent in drift mode, update the rulebook, run",
        "`python3 .github/scripts/official_drift.py --refresh`, and close this issue with the pull request.",
        "",
    ])


def refresh(baseline: Dict, fetch: Fetch) -> Dict:
    plugins = [dict(e, commit=latest_commit(e["repo"], e["path"], fetch)) for e in baseline.get("plugins", [])]
    pages = [dict(e, sha256=page_hash(e["url"], fetch)) for e in baseline.get("pages", [])]
    return dict(baseline, plugins=plugins, pages=pages)


def rule_sources(rules_dir: str) -> Dict[str, List[str]]:
    """Map each official source key to the rule IDs that cite it, read from the rule files."""
    sources: Dict[str, List[str]] = {}
    for name in sorted(os.listdir(rules_dir)):
        if not name.endswith(".md"):
            continue
        rule = None
        with open(os.path.join(rules_dir, name), encoding="utf-8") as handle:
            for line in handle:
                heading = _RULE.match(line)
                if heading:
                    rule = heading.group(1)
                source = _SOURCE.match(line.strip())
                if source and rule:
                    for key in (k.strip() for k in source.group(1).split(",")):
                        sources.setdefault(key, []).append(rule)
    return {key: sorted(rules) for key, rules in sources.items()}


def main(argv: Optional[List[str]] = None, fetch: Fetch = http_fetch) -> int:
    parser = argparse.ArgumentParser(description="Detect changes in the official sources of skill-maker.")
    parser.add_argument("--baseline", default=DEFAULT_BASELINE)
    parser.add_argument("--out", help="file for the issue body, written only on drift")
    parser.add_argument("--refresh", action="store_true", help="record the current commits and hashes")
    args = parser.parse_args(argv)
    with open(args.baseline, encoding="utf-8") as handle:
        baseline = json.load(handle)
    try:
        if args.refresh:
            updated = refresh(baseline, fetch)
            with open(args.baseline, "w", encoding="utf-8") as handle:
                json.dump(updated, handle, indent=2)
                handle.write("\n")
            return 0
        drift = find_drift(baseline, fetch)
    except FetchError as error:
        sys.stderr.write("official_drift: %s\n" % error)
        return 1
    if drift and args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(issue_body(drift))
    sys.stdout.write("%d source(s) changed\n" % len(drift))
    return 0


if __name__ == "__main__":
    sys.exit(main())
