"""Unit tests of .github/scripts/official_drift.py (no network: fetch is faked)."""

import hashlib
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, ".github", "scripts"))

import official_drift  # noqa: E402

API = "https://api.github.com/repos/anthropics/claude-plugins-official/commits?path=plugins/plugin-dev&per_page=1"
PAGE = "https://code.claude.com/docs/en/skills.md"


def baseline(commit="aaa", digest=None):
    return {
        "plugins": [{"key": "plugin-dev", "repo": "anthropics/claude-plugins-official",
                     "path": "plugins/plugin-dev", "commit": commit, "rules": ["C1", "C5"]}],
        "pages": [{"key": "docs-skills", "url": PAGE,
                   "sha256": digest or hashlib.sha256(b"page v1").hexdigest(), "rules": ["S1", "S4"]}],
    }


def fake(commit="aaa", page=b"page v1", status=200):
    def fetch(url):
        if url == API:
            return status, json.dumps([{"sha": commit}]).encode()
        if url == PAGE:
            return status, page
        raise AssertionError("unexpected url " + url)
    return fetch


class OfficialDriftTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = tmp.name
        self.baseline_path = os.path.join(self.dir, "baseline.json")
        self.out = os.path.join(self.dir, "drift.md")
        with open(self.baseline_path, "w", encoding="utf-8") as handle:
            json.dump(baseline(), handle)

    def run_cli(self, fetch, *extra):
        return official_drift.main(["--baseline", self.baseline_path, "--out", self.out] + list(extra), fetch)

    def test_no_drift_writes_nothing(self):
        self.assertEqual(self.run_cli(fake()), 0)
        self.assertFalse(os.path.exists(self.out))

    def test_plugin_commit_change_reported_with_compare_link(self):
        drift = official_drift.find_drift(baseline(), fake(commit="bbb"))
        self.assertEqual(drift, [{"key": "plugin-dev", "kind": "plugin", "old": "aaa", "new": "bbb",
                                  "link": "https://github.com/anthropics/claude-plugins-official/compare/aaa...bbb",
                                  "rules": ["C1", "C5"]}])

    def test_page_hash_change_reported(self):
        drift = official_drift.find_drift(baseline(), fake(page=b"page v2"))
        self.assertEqual([(d["key"], d["kind"], d["link"]) for d in drift], [("docs-skills", "page", PAGE)])
        self.assertEqual(drift[0]["new"], hashlib.sha256(b"page v2").hexdigest())

    def test_http_error_exits_1_and_writes_nothing(self):
        self.assertEqual(self.run_cli(fake(status=500)), 1)
        self.assertFalse(os.path.exists(self.out))

    def test_fetch_exception_exits_1(self):
        def broken(url):
            raise OSError("network down")
        self.assertEqual(self.run_cli(broken), 1)
        self.assertFalse(os.path.exists(self.out))

    def test_drift_writes_issue_body(self):
        self.assertEqual(self.run_cli(fake(commit="bbb", page=b"page v2")), 0)
        with open(self.out, encoding="utf-8") as handle:
            body = handle.read()
        self.assertIn("plugin-dev", body)
        self.assertIn("docs-skills", body)

    def test_issue_body_lists_keys_links_and_rules(self):
        body = official_drift.issue_body(official_drift.find_drift(baseline(), fake(commit="bbb")))
        self.assertIn("plugin-dev", body)
        self.assertIn("compare/aaa...bbb", body)
        self.assertIn("C1, C5", body)
        self.assertIn("Official drift", body)

    def test_refresh_updates_baseline(self):
        self.assertEqual(self.run_cli(fake(commit="bbb", page=b"page v2"), "--refresh"), 0)
        with open(self.baseline_path, encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(data["plugins"][0]["commit"], "bbb")
        self.assertEqual(data["pages"][0]["sha256"], hashlib.sha256(b"page v2").hexdigest())
        self.assertEqual(data["plugins"][0]["rules"], ["C1", "C5"])
        self.assertFalse(os.path.exists(self.out))

    def test_baseline_rules_match_rule_files(self):
        rules_dir = os.path.join(ROOT, "skill-maker", "shared", "rules")
        with open(os.path.join(ROOT, "skill-maker", "shared", "official-baseline.json"), encoding="utf-8") as handle:
            data = json.load(handle)
        recorded = {entry["key"]: sorted(entry["rules"]) for entry in data["plugins"] + data["pages"]}
        cited = official_drift.rule_sources(rules_dir)
        self.assertEqual({key: rules for key, rules in recorded.items() if rules}, cited)


class OpenIssueScriptTest(unittest.TestCase):
    """.github/scripts/open_drift_issue.sh with a fake gh that logs its calls."""

    def run_script(self, open_issue):
        import subprocess
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        log = os.path.join(tmp.name, "gh.log")
        fake = os.path.join(tmp.name, "gh")
        with open(fake, "w", encoding="utf-8") as handle:
            handle.write('#!/bin/sh\necho "$*" >> "%s"\n'
                         'case "$1 $2" in "issue list") printf "%%s" "%s";; esac\n' % (log, open_issue))
        os.chmod(fake, 0o755)
        body = os.path.join(tmp.name, "drift.md")
        with open(body, "w", encoding="utf-8") as handle:
            handle.write("changed\n")
        env = dict(os.environ, PATH=tmp.name + os.pathsep + os.environ.get("PATH", ""))
        done = subprocess.run(["bash", os.path.join(ROOT, ".github", "scripts", "open_drift_issue.sh"), body],
                              capture_output=True, text=True, env=env)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        with open(log, encoding="utf-8") as handle:
            return handle.read().splitlines()

    def test_no_open_issue_creates_one(self):
        calls = self.run_script("")
        self.assertTrue(calls[0].startswith("label create official-drift"))
        self.assertTrue(calls[-1].startswith("issue create"))
        self.assertIn("--label official-drift", calls[-1])

    def test_open_issue_gets_a_comment_not_a_second_issue(self):
        calls = self.run_script("42")
        self.assertTrue(calls[-1].startswith("issue comment 42"))
        self.assertFalse(any(call.startswith("issue create") for call in calls))


if __name__ == "__main__":
    unittest.main()
