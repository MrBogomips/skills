"""Offline tests for skills/pr-status/scripts/pr_status.py: no network, no real gh.

Run from the repo root: python3 -m unittest discover -s tests -p 'test_*.py'
"""
import contextlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "pr-status" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import pr_status as ps  # noqa: E402


def pr(**over):
    base = {
        "number": 7, "url": "https://github.com/acme/app/pull/7", "title": "A change", "state": "OPEN",
        "isDraft": False, "mergeable": "MERGEABLE", "mergeStateStatus": "CLEAN", "reviewDecision": "",
        "baseRefName": "main", "defaultBranch": "main", "author": {"login": "ann"},
        "reviews": [{"author": {"login": "bob", "__typename": "User"}, "state": "COMMENTED"}],
        "statusCheckRollup": [{"name": "build", "status": "COMPLETED", "conclusion": "SUCCESS"}],
    }
    base.update(over)
    return base


RED = {"name": "sbom", "status": "COMPLETED", "conclusion": "FAILURE"}
RUNNING = {"name": "e2e", "status": "IN_PROGRESS", "conclusion": ""}


class ParseRef(unittest.TestCase):
    def test_owner_repo_number(self):
        self.assertEqual(ps.parse_ref("acme/app#12"), ("acme/app", 12))

    def test_url(self):
        self.assertEqual(ps.parse_ref("https://github.com/acme/app/pull/12/files"), ("acme/app", 12))

    def test_dotted_repository_name(self):
        self.assertEqual(ps.parse_ref("acme/app.web#3"), ("acme/app.web", 3))

    def test_bare_number_uses_current_repository(self):
        self.assertEqual(ps.parse_ref("#12"), (None, 12))
        self.assertEqual(ps.parse_ref("12"), (None, 12))

    def test_rejects_anything_else(self):
        for bad in ("acme#12", "acme/app", "-R", "acme/app#0", "acme/app#x", "a/b/c#1", ""):
            with self.assertRaises(ValueError, msg=bad):
                ps.parse_ref(bad)


class Classify(unittest.TestCase):
    def state(self, **over):
        return ps.classify(pr(**over))["state"]

    def test_merged_and_closed_win_over_everything(self):
        self.assertEqual(self.state(state="MERGED", mergeable="UNKNOWN", mergeStateStatus="UNKNOWN"), "merged")
        self.assertEqual(self.state(state="CLOSED", mergeStateStatus="BLOCKED", statusCheckRollup=[RED]), "closed")

    def test_conflict_or_changes_requested_is_blocked(self):
        self.assertEqual(self.state(mergeable="CONFLICTING", mergeStateStatus="DIRTY"), "blocked")
        self.assertEqual(self.state(reviewDecision="CHANGES_REQUESTED", mergeStateStatus="BLOCKED"), "blocked")

    def test_blocked_wins_over_failed_checks_and_draft(self):
        self.assertEqual(self.state(mergeable="CONFLICTING", isDraft=True, statusCheckRollup=[RED]), "blocked")

    def test_failed_check_wins_over_draft(self):
        self.assertEqual(self.state(isDraft=True, mergeStateStatus="DRAFT", statusCheckRollup=[RED]), "ci_failed")

    def test_failed_check_says_whether_the_merge_is_blocked(self):
        facts = ps.classify(pr(mergeStateStatus="UNSTABLE", statusCheckRollup=[RED]))
        self.assertEqual(facts["state"], "ci_failed")
        self.assertEqual(facts["failed_checks"], ["sbom"])
        self.assertTrue(facts["failed_checks_not_required"])
        facts = ps.classify(pr(mergeStateStatus="BLOCKED", statusCheckRollup=[RED]))
        self.assertFalse(facts["failed_checks_not_required"])

    def test_status_context_failure_counts(self):
        self.assertEqual(self.state(statusCheckRollup=[{"context": "ci/x", "state": "ERROR"}]), "ci_failed")

    def test_draft(self):
        self.assertEqual(self.state(isDraft=True, mergeStateStatus="DRAFT", reviews=[]), "draft")

    def test_no_review_is_unreviewed_whatever_review_decision_says(self):
        self.assertEqual(self.state(reviews=[], reviewDecision="REVIEW_REQUIRED"), "unreviewed")

    def test_review_required_with_comment_reviews_is_not_unreviewed(self):
        self.assertEqual(self.state(reviewDecision="REVIEW_REQUIRED", mergeStateStatus="BLOCKED"), "in_progress")

    def test_author_replies_are_not_reviews(self):
        self.assertEqual(self.state(reviews=[{"author": {"login": "ann"}, "state": "COMMENTED"}]), "unreviewed")

    def test_bot_and_pending_reviews_are_not_reviews(self):
        reviews = [{"author": {"login": "copilot-pull-request-reviewer", "__typename": "Bot"}, "state": "COMMENTED"},
                   {"author": {"login": "bob", "__typename": "User"}, "state": "PENDING"},
                   {"author": None, "state": "COMMENTED"}]
        facts = ps.classify(pr(reviews=reviews))
        self.assertEqual((facts["state"], facts["reviews"], facts["bot_reviews"]), ("unreviewed", 0, 1))

    def test_dismissed_review_is_a_review(self):
        self.assertEqual(self.state(reviews=[{"author": {"login": "bob", "__typename": "User"},
                                              "state": "DISMISSED"}]), "in_progress")

    def test_rerun_that_passed_clears_the_failure(self):
        old = dict(RED, name="build", workflowName="CI", startedAt="2026-01-01T10:00:00Z")
        new = {"name": "build", "workflowName": "CI", "status": "COMPLETED", "conclusion": "SUCCESS",
               "startedAt": "2026-01-01T11:00:00Z"}
        for order in ([old, new], [new, old]):
            facts = ps.classify(pr(statusCheckRollup=order))
            self.assertEqual((facts["state"], facts["failed_checks"]), ("in_progress", []))

    def test_rerun_in_progress_replaces_the_failure(self):
        old = dict(RED, name="build", workflowName="CI", startedAt="2026-01-01T10:00:00Z")
        new = {"name": "build", "workflowName": "CI", "status": "IN_PROGRESS", "conclusion": None,
               "startedAt": "2026-01-01T11:00:00Z"}
        facts = ps.classify(pr(statusCheckRollup=[old, new]))
        self.assertEqual((facts["state"], facts["pending_checks"]), ("in_progress", ["build"]))

    def test_same_name_in_two_workflows_are_two_checks(self):
        red = dict(RED, name="build", workflowName="Nightly", startedAt="2026-01-01T10:00:00Z")
        green = {"name": "build", "workflowName": "CI", "status": "COMPLETED", "conclusion": "SUCCESS",
                 "startedAt": "2026-01-01T11:00:00Z"}
        self.assertEqual(self.state(statusCheckRollup=[red, green]), "ci_failed")

    def test_stale_check_is_ignored_and_expected_status_is_pending(self):
        stale = {"name": "old", "status": "COMPLETED", "conclusion": "STALE"}
        expected = {"context": "ci/required", "state": "EXPECTED"}
        facts = ps.classify(pr(statusCheckRollup=[stale, expected]))
        self.assertEqual((facts["failed_checks"], facts["pending_checks"]), ([], ["ci/required"]))

    def test_base_is_default(self):
        self.assertTrue(ps.classify(pr())["base_is_default"])
        facts = ps.classify(pr(baseRefName="feature/x"))
        self.assertFalse(facts["base_is_default"])
        self.assertEqual(facts["default_branch"], "main")

    def test_blocked_merge_state_with_running_checks_is_in_progress(self):
        facts = ps.classify(pr(mergeStateStatus="BLOCKED", statusCheckRollup=[RUNNING]))
        self.assertEqual(facts["state"], "in_progress")
        self.assertEqual(facts["pending_checks"], ["e2e"])

    def test_unknown_merge_state_is_reported_not_blocked(self):
        facts = ps.classify(pr(mergeable="UNKNOWN", mergeStateStatus="UNKNOWN"))
        self.assertEqual(facts["state"], "in_progress")
        self.assertTrue(facts["merge_state_unknown"])

    def test_emoji_and_identity(self):
        facts = ps.classify(pr(state="MERGED"))
        self.assertEqual((facts["emoji"], facts["repo"], facts["number"]), ("✅", "acme/app", 7))
        self.assertEqual(facts["url"], "https://github.com/acme/app/pull/7")
        self.assertEqual(set(ps.EMOJI), {"merged", "closed", "blocked", "ci_failed", "draft", "unreviewed",
                                         "in_progress", "error"})

    def test_approved_and_base(self):
        facts = ps.classify(pr(reviewDecision="APPROVED", baseRefName="feature/x"))
        self.assertTrue(facts["approved"])
        self.assertEqual(facts["base"], "feature/x")


def envelope(**over):
    """The GraphQL answer gh prints for one pull request, from the flat fixture."""
    flat = pr(**over)
    checks = []
    for c in flat["statusCheckRollup"]:
        if "context" in c:
            checks.append({"__typename": "StatusContext", "context": c["context"], "state": c["state"],
                           "createdAt": c.get("startedAt")})
        else:
            workflow = {"workflowRun": {"workflow": {"name": c["workflowName"]}}} if c.get("workflowName") else None
            checks.append({"__typename": "CheckRun", "name": c["name"], "status": c["status"],
                           "conclusion": c.get("conclusion"), "startedAt": c.get("startedAt"),
                           "checkSuite": workflow})
    node = {k: flat[k] for k in ("number", "url", "title", "state", "isDraft", "mergeable", "mergeStateStatus",
                                 "reviewDecision", "baseRefName", "author")}
    node["reviews"] = {"nodes": flat["reviews"]}
    node["commits"] = {"nodes": [{"commit": {"statusCheckRollup": {"contexts": {"nodes": checks}}}}]}
    return {"data": {"repository": {"defaultBranchRef": {"name": flat["defaultBranch"]}, "pullRequest": node}}}


class Fetch(unittest.TestCase):
    def runner(self, answers):
        calls = []

        def run(args):
            calls.append(args)
            if args[:3] == ["gh", "repo", "view"]:
                return json.dumps({"nameWithOwner": "here/now"})
            answer = answers[min(len(calls), len(answers)) - 1]
            if isinstance(answer, Exception):
                raise answer
            return json.dumps(answer)
        return run, calls

    def test_normalizes_the_graphql_answer(self):
        run, calls = self.runner([envelope(statusCheckRollup=[dict(RED, workflowName="CI"),
                                                              {"context": "ci/x", "state": "PENDING"}])])
        data = ps.fetch("acme/app", 7, run=run, sleep=lambda s: None)
        self.assertEqual(data["defaultBranch"], "main")
        self.assertEqual(data["reviews"][0]["author"]["login"], "bob")
        self.assertEqual(data["statusCheckRollup"][0]["workflowName"], "CI")
        self.assertEqual(data["statusCheckRollup"][1], {"context": "ci/x", "state": "PENDING", "startedAt": None})
        self.assertEqual(calls[0][:3], ["gh", "api", "graphql"])
        self.assertIn("owner=acme", calls[0])
        self.assertIn("number=7", calls[0])

    def test_rereads_while_merge_state_is_unknown(self):
        run, calls = self.runner([envelope(mergeable="UNKNOWN", mergeStateStatus="UNKNOWN"), envelope()])
        data = ps.fetch("acme/app", 7, run=run, sleep=lambda s: None)
        self.assertEqual(data["mergeable"], "MERGEABLE")
        self.assertEqual(len(calls), 2)

    def test_gives_up_after_the_retries(self):
        run, calls = self.runner([envelope(mergeable="UNKNOWN")])
        data = ps.fetch("acme/app", 7, run=run, sleep=lambda s: None)
        self.assertEqual(data["mergeable"], "UNKNOWN")
        self.assertEqual(len(calls), ps.UNKNOWN_READS)

    def test_merged_pr_is_read_once(self):
        run, calls = self.runner([envelope(state="MERGED", mergeable="UNKNOWN")])
        ps.fetch("acme/app", 7, run=run, sleep=lambda s: None)
        self.assertEqual(len(calls), 1)

    def test_missing_pull_request_is_an_error(self):
        run, _ = self.runner([{"data": {"repository": {"defaultBranchRef": None, "pullRequest": None}}}])
        with self.assertRaises(ps.GhError):
            ps.fetch("acme/app", 7, run=run, sleep=lambda s: None)

    def test_bare_number_is_resolved_to_the_current_repository_once(self):
        run, calls = self.runner([envelope()])
        out = ps.collect(["#7", "8"], run=run, sleep=lambda s: None)
        self.assertEqual([e["ref"] for e in out], ["here/now#7", "here/now#8"])
        self.assertEqual(sum(1 for c in calls if c[:3] == ["gh", "repo", "view"]), 1)
        self.assertIn("owner=here", calls[1])

    def test_collect_keeps_going_after_one_failure(self):
        run, _ = self.runner([ps.GhError("Could not resolve to a PullRequest"), envelope()])
        out = ps.collect(["acme/app#1", "acme/app#7", "nonsense"], run=run, sleep=lambda s: None)
        self.assertEqual([e.get("state") for e in out], ["error", "in_progress", "error"])
        self.assertIn("Could not resolve", out[0]["error"])
        self.assertEqual((out[0]["ref"], out[0]["emoji"]), ("acme/app#1", ps.EMOJI["error"]))


class Main(unittest.TestCase):
    def call(self, argv, entries, gh="/usr/bin/gh"):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(ps.shutil, "which", return_value=gh), \
                mock.patch.object(ps, "collect", return_value=entries), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            return ps.main(argv), out.getvalue(), err.getvalue()

    def test_exit_codes(self):
        ok = [{"ref": "a/b#1", "state": "merged"}]
        self.assertEqual(self.call(["a/b#1"], ok)[0], 0)
        self.assertEqual(self.call(["a/b#1"], ok + [{"ref": "x", "state": "error", "error": "e"}])[0], 1)
        self.assertEqual(self.call([], ok)[0], 2)
        code, _, err = self.call(["a/b#1"], ok, gh=None)
        self.assertEqual(code, 3)
        self.assertIn("gh auth login", err)

    def test_prints_json(self):
        _, out, _ = self.call(["a/b#1"], [{"ref": "a/b#1", "state": "merged"}])
        self.assertEqual(json.loads(out)[0]["ref"], "a/b#1")


class RunGh(unittest.TestCase):
    def test_returns_stdout_and_reports_the_first_stderr_line(self):
        done = subprocess.CompletedProcess([], 0, stdout="{}", stderr="hint: ignore me")
        with mock.patch.object(ps.subprocess, "run", return_value=done):
            self.assertEqual(ps.run_gh(["gh"]), "{}")
        failed = subprocess.CompletedProcess([], 1, stdout="", stderr="gh: Not Found\nmore")
        with mock.patch.object(ps.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(ps.GhError, "^gh: Not Found$"):
                ps.run_gh(["gh"])


class Cli(unittest.TestCase):
    def test_no_arguments_is_a_usage_error(self):
        done = subprocess.run([sys.executable, str(SCRIPTS / "pr_status.py")], capture_output=True, text=True)
        self.assertEqual(done.returncode, 2)
        self.assertIn("usage", done.stderr.lower())


if __name__ == "__main__":
    unittest.main()
