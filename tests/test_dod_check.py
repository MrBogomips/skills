"""Offline tests for skills/done/scripts/dod_check.sh: temporary git repositories, a bare remote, a stub gh.

Run from the repo root: python3 -m unittest discover -s tests -p 'test_*.py'
"""
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "done" / "scripts" / "dod_check.sh"
BASH = "/bin/bash" if os.path.exists("/bin/bash") else shutil.which("bash")
FAKE_GITHUB_URL = "https://github.com/example/project.git"

GH_STUB = """#!/bin/sh
# Stub gh: answers from GH_STUB_PR_VIEW (one TSV line) and GH_STUB_MERGED (TSV lines), or runs the
# caller's --jq expression over GH_STUB_PR_JSON / GH_STUB_MERGED_JSON, as the real gh does.
command="$1 $2"
jq_expr=""
while [ $# -gt 0 ]; do
    if [ "$1" = "--jq" ]; then jq_expr="$2"; fi
    shift
done
case "$command" in
    "pr view")
        if [ -n "${GH_STUB_PR_JSON:-}" ]; then printf '%s' "$GH_STUB_PR_JSON" | jq -r "$jq_expr"; exit $?; fi
        if [ -n "${GH_STUB_PR_VIEW:-}" ]; then printf '%s\\n' "$GH_STUB_PR_VIEW"; exit 0; fi
        if [ -n "${GH_STUB_AUTH_ERROR:-}" ]; then echo "gh auth login required" >&2; exit 4; fi
        echo "no pull requests found for branch" >&2; exit 1 ;;
    "pr list")
        if [ -n "${GH_STUB_LOG:-}" ]; then echo "pr list" >> "$GH_STUB_LOG"; fi
        if [ -n "${GH_STUB_MERGED_JSON:-}" ]; then printf '%s' "$GH_STUB_MERGED_JSON" | jq -r "$jq_expr"; exit $?; fi
        if [ -n "${GH_STUB_MERGED:-}" ]; then printf '%s\\n' "$GH_STUB_MERGED"; fi
        exit 0 ;;
    "run list")
        if [ -n "${GH_STUB_RUNS_JSON:-}" ]; then printf '%s' "$GH_STUB_RUNS_JSON" | jq -r "$jq_expr"; exit $?; fi
        if [ -n "${GH_STUB_RUNS:-}" ]; then printf '%s\\n' "$GH_STUB_RUNS"; exit 0; fi
        echo none; exit 0 ;;
    "api graphql")
        printf '%s\\n' "${GH_STUB_THREADS:-0}"; exit 0 ;;
esac
exit 1
"""


def parse(output):
    """Returns {key: (value, [indented lines below the key, indentation kept])}."""
    result, current = {}, None
    for line in output.splitlines():
        if line.startswith(" "):
            result[current][1].append(line)
        elif ": " in line or line.endswith(":"):
            key, _, value = line.partition(":")
            current = key
            result[key] = (value.strip(), [])
    return result


class DodCheckCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dodcheck-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.env = {
            "PATH": os.environ["PATH"],
            "HOME": str(self.tmp),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.com",
            "DOD_CHECK_GH": "gh-not-installed-for-tests",
        }
        self.remote = self.tmp / "remote.git"
        self.repo = self.tmp / "repo"
        self.git("init", "-q", "--bare", "-b", "main", str(self.remote), cwd=self.tmp)
        self.git("init", "-q", "-b", "main", str(self.repo), cwd=self.tmp)
        self.git("remote", "add", "origin", str(self.remote))
        self.write("README.md", "hello\n")
        self.commit("init")
        self.git("push", "-q", "-u", "origin", "main")

    def git(self, *args, cwd=None):
        done = subprocess.run(["git", *args], cwd=cwd or self.repo, env=self.env,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout.strip()

    def write(self, rel, text="x\n", repo=None):
        path = (repo or self.repo) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def use_stub_gh(self, **stub_env):
        stub = self.tmp / "gh-stub"
        stub.write_text(GH_STUB)
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
        self.env["DOD_CHECK_GH"] = str(stub)
        self.env.update(stub_env)
        # The bare remote stays reachable while the configured URL looks like GitHub.
        self.git("config", f"url.{self.remote}.insteadOf", FAKE_GITHUB_URL)
        self.git("config", "remote.origin.url", FAKE_GITHUB_URL)

    def run_script(self, *args, cwd=None, expect=0):
        done = subprocess.run([BASH, str(SCRIPT), *args], cwd=cwd or self.repo, env=self.env,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, expect, done.stdout + done.stderr)
        return parse(done.stdout)

    def items(self, out, key):
        return [line.strip() for line in out[key][1]]


class RepositoryState(DodCheckCase):
    def test_outside_git(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        (plain / "DoD.md").write_text("# Definition of Done\n")
        out = self.run_script(cwd=plain)
        self.assertEqual(out["git"][0], "no")
        self.assertEqual(out["root"][0], str(plain))
        self.assertEqual(out["dod_files"][0], "1")
        self.assertEqual(self.items(out, "dod_files"), ["DoD.md"])
        self.assertNotIn("branch", out)

    def test_clean_pushed_repository(self):
        out = self.run_script()
        expected = {
            "git": "yes", "root": str(self.repo), "branch": "main", "integration_branch": "main",
            "remote": "origin", "fetch": "ok", "upstream": "origin/main", "ahead": "0", "behind": "0",
            "integration_behind": "0", "modified": "0", "untracked": "0", "stashes": "0",
            "extra_worktrees": "0", "forge": "unknown", "merged_branches": "0",
            "changed_paths": "0", "dod_files": "0",
        }
        for key, value in expected.items():
            self.assertEqual(out[key][0], value, key)
        self.assertNotIn("pr_number", out)

    def test_dirty_untracked_unpushed(self):
        self.write("src/a.py")
        self.commit("local only")
        self.write("README.md", "changed\n")
        self.write("notes draft.txt")
        self.git("stash", "push", "-q", "-m", "s", "--", "README.md")
        self.write("README.md", "changed again\n")
        out = self.run_script()
        self.assertEqual(out["ahead"][0], "1")
        self.assertEqual(out["modified"][0], "1")
        self.assertEqual(self.items(out, "modified"), ["README.md"])
        self.assertEqual(self.items(out, "untracked"), ["notes draft.txt"])
        self.assertEqual(out["stashes"][0], "1")
        self.assertEqual(self.items(out, "changed_paths"), ["README.md", "notes draft.txt", "src/a.py"])

    def test_topic_branch_without_upstream(self):
        self.git("checkout", "-q", "-b", "feature/x")
        self.write("x.txt")
        self.commit("x")
        out = self.run_script()
        self.assertEqual(out["branch"][0], "feature/x")
        self.assertEqual(out["upstream"][0], "none")
        self.assertEqual(out["integration_branch"][0], "main")
        self.assertEqual(self.items(out, "changed_paths"), ["x.txt"])
        self.assertNotIn("ahead", out)

    def test_stale_integration_branch_and_fetch(self):
        other = self.tmp / "other"
        self.git("clone", "-q", str(self.remote), str(other), cwd=self.tmp)
        self.write("new.txt", repo=other)
        self.git("add", "-A", cwd=other)
        self.git("commit", "-q", "-m", "remote work", cwd=other)
        self.git("push", "-q", "origin", "main", cwd=other)
        self.git("checkout", "-q", "-b", "feature/y")
        out = self.run_script("--no-fetch")
        self.assertEqual(out["fetch"][0], "skipped")
        self.assertEqual(out["integration_behind"][0], "0")
        out = self.run_script()
        self.assertEqual(out["fetch"][0], "ok")
        self.assertEqual(out["integration_behind"][0], "1")

    def test_base_option_and_fallback_detection(self):
        self.git("checkout", "-q", "-b", "develop")
        self.git("push", "-q", "-u", "origin", "develop")
        self.git("checkout", "-q", "-b", "feature/z")
        # Without origin/HEAD (never fetched), the first well-known name that exists wins.
        self.assertEqual(self.run_script("--no-fetch")["integration_branch"][0], "develop")
        self.assertEqual(self.run_script("--no-fetch", "--base", "main")["integration_branch"][0], "main")
        self.git("remote", "set-head", "origin", "main")
        self.assertEqual(self.run_script("--no-fetch")["integration_branch"][0], "main")

    def test_unreachable_remote_reports_failed_fetch(self):
        self.git("remote", "set-url", "origin", str(self.tmp / "gone.git"))
        out = self.run_script()
        self.assertEqual(out["fetch"][0], "failed")
        self.assertEqual(out["branch"][0], "main")

    def test_repository_without_commits(self):
        empty = self.tmp / "empty"
        self.git("init", "-q", "-b", "main", str(empty), cwd=self.tmp)
        self.write("a.txt", repo=empty)
        out = self.run_script(cwd=empty)
        self.assertEqual(out["git"][0], "yes")
        self.assertEqual(out["head"][0], "none")
        self.assertEqual(self.items(out, "untracked"), ["a.txt"])

    def test_detached_head(self):
        self.git("checkout", "-q", "--detach")
        out = self.run_script()
        self.assertEqual(out["branch"][0], "(detached)")
        self.assertEqual(out["upstream"][0], "none")

    def test_extra_worktree_counted(self):
        self.git("worktree", "add", "-q", str(self.tmp / "wt"), "-b", "wt-branch")
        self.assertEqual(self.run_script()["extra_worktrees"][0], "1")

    def test_list_cap(self):
        for i in range(5):
            self.write(f"u{i}.txt")
        out = self.run_script("--max-list", "2")
        self.assertEqual(out["untracked"][0], "5")
        self.assertEqual(self.items(out, "untracked"), ["u0.txt", "u1.txt", "... (+3 more)"])

    def test_usage_errors(self):
        self.run_script("--bogus", expect=2)
        self.run_script("--base", expect=2)
        self.run_script("--max-list", "x", expect=2)
        self.run_script("--base", "nope", expect=2)

    def test_base_accepts_remote_prefix(self):
        self.git("checkout", "-q", "-b", "feature/b")
        self.write("b.txt")
        self.commit("b")
        out = self.run_script("--base", "origin/main")
        self.assertEqual(out["integration_branch"][0], "main")
        self.assertEqual(self.items(out, "changed_paths"), ["b.txt"])

    def test_remote_not_named_origin(self):
        self.git("remote", "rename", "origin", "upstream")
        self.git("checkout", "-q", "-b", "feature/r")
        self.write("r.txt")
        self.commit("r")
        out = self.run_script()
        self.assertEqual(out["remote"][0], "upstream")
        self.assertEqual(out["fetch"][0], "ok")
        self.assertEqual(out["integration_branch"][0], "main")
        self.assertEqual(out["integration_behind"][0], "0")
        self.assertEqual(self.items(out, "changed_paths"), ["r.txt"])

    def test_no_remote(self):
        self.git("remote", "remove", "origin")
        out = self.run_script()
        self.assertEqual(out["remote"][0], "none")
        self.assertEqual(out["fetch"][0], "skipped")
        self.assertEqual(out["integration_branch"][0], "main")
        self.assertEqual(out["forge"][0], "unknown")

    def test_rename_reports_both_paths(self):
        self.write("pkg/y.txt", "content that stays the same\n" * 5)
        self.commit("y")
        self.git("push", "-q", "origin", "main")
        self.git("mv", "pkg/y.txt", "moved.txt")
        self.assertEqual(self.items(self.run_script(), "changed_paths"), ["moved.txt", "pkg/y.txt"])


class MergedBranches(DodCheckCase):
    def make_branch(self, name, push=True):
        self.git("checkout", "-q", "-b", name)
        self.write(name.replace("/", "-") + ".txt")
        self.commit(name)
        if push:
            self.git("push", "-q", "-u", "origin", name)
        tip = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "main")
        return tip

    def test_merged_by_ancestry(self):
        self.make_branch("feature/merged")
        self.git("merge", "-q", "--ff-only", "feature/merged")
        self.git("push", "-q", "origin", "main")
        self.make_branch("feature/open", push=False)
        out = self.run_script()
        self.assertEqual(out["merged_branches"][0], "1")
        self.assertEqual(self.items(out, "merged_branches"), ["feature/merged remote=yes via=ancestor"])

    def test_squash_merged_through_forge(self):
        tip = self.make_branch("feature/squashed", push=False)
        moved = self.make_branch("feature/moved", push=False)
        self.use_stub_gh(GH_STUB_MERGED=f"feature/squashed\t{tip}\nfeature/moved\t{'0' * 40}")
        out = self.run_script()
        self.assertEqual(out["gh"][0], "ok")
        self.assertEqual(self.items(out, "merged_branches"), ["feature/squashed remote=no via=pr"])
        self.assertNotEqual(moved, "0" * 40)

    def test_current_branch_marked_and_integration_branch_never_listed(self):
        self.make_branch("feature/cur")
        self.git("merge", "-q", "--ff-only", "feature/cur")
        self.git("push", "-q", "origin", "main")
        self.git("checkout", "-q", "feature/cur")
        out = self.run_script()
        self.assertEqual(self.items(out, "merged_branches"), ["feature/cur remote=yes via=ancestor current=yes"])
        self.git("checkout", "-q", "-b", "develop")
        self.assertEqual(len(self.items(self.run_script("--base", "develop"), "merged_branches")), 1)

    def test_current_branch_squash_merged(self):
        tip = self.make_branch("feature/sq", push=False)
        self.git("checkout", "-q", "feature/sq")
        self.use_stub_gh(GH_STUB_MERGED=f"feature/sq\t{tip}",
                         GH_STUB_PR_VIEW=f"5\tMERGED\tfalse\tAPPROVED\tpass\t{tip}")
        out = self.run_script()
        self.assertEqual(self.items(out, "merged_branches"), ["feature/sq remote=no via=pr current=yes"])
        self.assertEqual(out["pr_head_matches"][0], "yes")


class PullRequest(DodCheckCase):
    def test_pr_fields(self):
        self.git("checkout", "-q", "-b", "feature/pr")
        self.use_stub_gh(GH_STUB_PR_VIEW=f"12\tOPEN\tfalse\tAPPROVED\tpass\t{self.git('rev-parse', 'HEAD')}")
        out = self.run_script()
        self.assertEqual(out["pr_head_matches"][0], "yes")
        self.assertEqual(out["forge"][0], "github")
        self.assertEqual(out["gh"][0], "ok")
        for key, value in {"pr_number": "12", "pr_state": "OPEN", "pr_draft": "false",
                           "pr_review": "APPROVED", "pr_checks": "pass"}.items():
            self.assertEqual(out[key][0], value, key)

    def test_merged_pr_of_an_earlier_state(self):
        self.git("checkout", "-q", "-b", "feature/reused")
        old = self.git("rev-parse", "HEAD")
        self.write("later.txt")
        self.commit("work after the merge")
        self.use_stub_gh(GH_STUB_PR_VIEW=f"12\tMERGED\tfalse\tAPPROVED\tpass\t{old}",
                         GH_STUB_MERGED=f"feature/reused\t{old}")
        out = self.run_script()
        self.assertEqual(out["pr_state"][0], "MERGED")
        self.assertEqual(out["pr_head_matches"][0], "no")
        self.assertEqual(out["merged_branches"][0], "0")

    def test_no_pr_for_branch(self):
        self.git("checkout", "-q", "-b", "feature/nopr")
        self.use_stub_gh()
        out = self.run_script()
        self.assertEqual(out["gh"][0], "ok")
        self.assertEqual(out["pr_number"][0], "none")
        self.assertNotIn("pr_state", out)

    def test_empty_review_decision(self):
        self.git("checkout", "-q", "-b", "feature/noreview")
        self.use_stub_gh(GH_STUB_PR_VIEW="7\tOPEN\ttrue\t\tpending\tabc")
        out = self.run_script()
        self.assertEqual(out["pr_review"][0], "none")
        self.assertEqual(out["pr_checks"][0], "pending")

    def test_unauthenticated(self):
        self.git("checkout", "-q", "-b", "feature/auth")
        self.use_stub_gh(GH_STUB_AUTH_ERROR="1")
        out = self.run_script()
        self.assertEqual(out["gh"][0], "unauthenticated")
        self.assertNotIn("pr_number", out)

    def test_gh_missing(self):
        self.use_stub_gh()
        self.env["DOD_CHECK_GH"] = "gh-not-installed-for-tests"
        out = self.run_script()
        self.assertEqual(out["forge"][0], "github")
        self.assertEqual(out["gh"][0], "missing")
        self.assertNotIn("pr_number", out)

    def test_no_pr_lookup_on_integration_branch(self):
        self.use_stub_gh(GH_STUB_PR_VIEW="12\tOPEN\tfalse\tAPPROVED\tpass")
        self.assertNotIn("pr_number", self.run_script())


@unittest.skipUnless(shutil.which("jq"), "jq not installed")
class GhQueries(DodCheckCase):
    """Runs the script's own --jq expressions over GitHub-shaped JSON."""

    def view(self, rollup, review="APPROVED"):
        self.git("checkout", "-q", "-B", "feature/q")
        head = self.git("rev-parse", "HEAD")
        self.use_stub_gh(GH_STUB_PR_JSON=json.dumps({
            "number": 9, "state": "OPEN", "isDraft": False, "reviewDecision": review,
            "statusCheckRollup": rollup, "headRefOid": head}))
        return self.run_script()

    def test_checks_classification(self):
        check = {"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "SUCCESS"}
        cases = [
            ([], "none"),
            (None, "none"),
            ([check], "pass"),
            ([check, {"__typename": "CheckRun", "status": "IN_PROGRESS", "conclusion": ""}], "pending"),
            ([check, {"__typename": "StatusContext", "state": "PENDING"}], "pending"),
            ([check, {"__typename": "StatusContext", "state": "FAILURE"}], "fail"),
            ([{"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "TIMED_OUT"}], "fail"),
            ([check, {"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "SKIPPED"}], "pass"),
        ]
        for rollup, expected in cases:
            with self.subTest(expected=expected, rollup=rollup):
                out = self.view(rollup)
                self.assertEqual(out["pr_checks"][0], expected)
                self.assertEqual(out["pr_number"][0], "9")
                self.assertEqual(out["pr_head_matches"][0], "yes")

    def test_null_review_decision(self):
        self.assertEqual(self.view([], review=None)["pr_review"][0], "none")

    def test_ci_head_classification(self):
        cases = [
            ([], "none"),
            ([{"status": "completed", "conclusion": "success"}], "pass"),
            ([{"status": "completed", "conclusion": "success"}, {"status": "in_progress", "conclusion": ""}], "pending"),
            ([{"status": "completed", "conclusion": "failure"}], "fail"),
            ([{"status": "completed", "conclusion": "skipped"}], "pass"),
        ]
        for runs, expected in cases:
            with self.subTest(expected=expected):
                self.use_stub_gh(GH_STUB_RUNS_JSON=json.dumps(runs))
                self.assertEqual(self.run_script()["ci_head"][0], expected)

    def test_merged_list_query(self):
        self.git("checkout", "-q", "-b", "feature/done-one")
        self.write("one.txt")
        self.commit("one")
        tip = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "main")
        self.use_stub_gh(GH_STUB_MERGED_JSON=json.dumps([{"headRefName": "feature/done-one", "headRefOid": tip}]))
        self.assertEqual(self.items(self.run_script(), "merged_branches"), ["feature/done-one remote=no via=pr"])


class DodHierarchy(DodCheckCase):
    def setUp(self):
        super().setUp()
        for rel in ("DoD.md", "packages/api/DoD.md", "docs/DoD.md"):
            self.write(rel, "# Definition of Done\n")
        self.write("packages/api/src/x.ts")
        self.write("packages/web/y.ts")
        self.write("docs/guide.md")
        self.commit("layout")
        self.git("push", "-q", "origin", "main")
        self.git("checkout", "-q", "-b", "feature/h")

    def test_chain_most_specific_first(self):
        self.write("packages/api/src/x.ts", "changed\n")
        self.write("README.md", "changed\n")
        self.commit("work")
        self.write("packages/api/src/deep/new file.ts")
        out = self.run_script()
        self.assertEqual(out["dod_files"][0], "2")
        self.assertEqual(out["dod_files"][1], ["  packages/api/DoD.md paths=2", "  DoD.md paths=1"])
        self.assertNotIn("no_dod_paths", out)

    def test_ancestor_dod_listed_even_without_nearest_paths(self):
        self.write("packages/api/src/x.ts", "changed\n")
        out = self.run_script()
        self.assertEqual(out["dod_files"][1], ["  packages/api/DoD.md paths=1", "  DoD.md paths=0"])

    def test_root_dod_reported_without_changes(self):
        out = self.run_script()
        self.assertEqual(out["changed_paths"][0], "0")
        self.assertEqual(out["dod_files"][1], ["  DoD.md paths=0"])

    def test_untracked_nested_repository_is_not_entered(self):
        nested = self.repo / "vendor" / "lib"
        nested.mkdir(parents=True)
        self.git("init", "-q", "-b", "main", str(nested))
        self.write("vendor/lib/DoD.md")
        self.write("vendor/lib/a.txt")
        self.git("add", "-A", cwd=nested)
        self.git("commit", "-q", "-m", "nested", cwd=nested)
        out = self.run_script()
        self.assertEqual(self.items(out, "untracked"), ["vendor/lib/"])
        self.assertEqual(out["dod_files"][1], ["  DoD.md paths=1"])

    def test_rename_out_of_a_subtree_loads_its_dod(self):
        self.git("mv", "packages/api/src/x.ts", "moved.ts")
        out = self.run_script()
        self.assertEqual(out["dod_files"][1], ["  packages/api/DoD.md paths=1", "  DoD.md paths=1"])

    def test_deleted_file_in_removed_directory(self):
        self.git("rm", "-q", "-r", "packages/web")
        self.commit("drop web")
        out = self.run_script()
        self.assertEqual(out["dod_files"][1], ["  DoD.md paths=1"])

    def test_paths_without_any_dod(self):
        self.git("rm", "-q", "DoD.md")
        self.commit("no root dod")
        self.git("push", "-q", "origin", "HEAD:main")
        self.write("packages/web/y.ts", "changed\n")
        self.write("docs/guide.md", "changed\n")
        out = self.run_script()
        self.assertEqual(out["dod_files"][1], ["  docs/DoD.md paths=1"])
        self.assertEqual(out["no_dod_paths"][0], "1")
        self.assertEqual(self.items(out, "no_dod_paths"), ["packages/web/y.ts"])

    def test_case_variant_name_is_honored(self):
        self.git("mv", "packages/api/DoD.md", "packages/api/DOD.md")
        self.commit("rename")
        self.git("push", "-q", "origin", "HEAD:main")
        self.write("packages/api/src/x.ts", "changed\n")
        out = self.run_script()
        self.assertEqual(out["dod_files"][1][0], "  packages/api/DOD.md paths=1")

    def test_two_spellings_in_one_directory(self):
        probe = self.tmp / "CaseProbe"
        probe.touch()
        if (self.tmp / "caseprobe").exists():
            self.skipTest("case-insensitive filesystem")
        self.write("packages/api/dod.md")
        out = self.run_script()
        self.assertEqual(self.items(out, "dod_name_conflict"), ["packages/api"])


class Extensions(DodCheckCase):
    """head_tree, --since, debug markers, CI of HEAD, review threads, lazy merged-PR lookup."""

    def test_head_tree_survives_a_new_commit_with_the_same_tree(self):
        tree = self.run_script()["head_tree"][0]
        self.git("commit", "-q", "--allow-empty", "-m", "empty")
        self.assertEqual(self.run_script()["head_tree"][0], tree)
        self.assertEqual(tree, self.git("rev-parse", "HEAD^{tree}"))

    def test_since_adds_pushed_commits_on_the_integration_branch(self):
        start = self.git("rev-parse", "HEAD")
        self.write("pushed.txt")
        self.commit("pushed work")
        self.git("push", "-q", "origin", "main")
        self.assertEqual(self.run_script()["changed_paths"][0], "0")
        self.assertEqual(self.items(self.run_script("--since", start), "changed_paths"), ["pushed.txt"])
        self.run_script("--since", "no-such-rev", expect=2)

    def test_debug_markers_in_added_lines_only(self):
        self.write("old.js", "console.log('kept')\n")
        self.commit("old")
        self.git("push", "-q", "origin", "main")
        self.git("checkout", "-q", "-b", "feature/dbg")
        self.write("a.js", "let x = 1;\nconsole.log(x);\ndebugger;\n")
        self.commit("debug")
        self.write("b.py", "import pdb; pdb.set_trace()\n")
        out = self.run_script()
        self.assertEqual(out["debug_markers"][0], "3")
        self.assertEqual(self.items(out, "debug_markers"),
                         ["a.js:2: console.log(x);", "a.js:3: debugger;", "b.py:1: import pdb; pdb.set_trace()"])

    def test_ci_of_head_on_the_integration_branch(self):
        self.use_stub_gh(GH_STUB_RUNS="fail")
        out = self.run_script()
        self.assertEqual(out["ci_head"][0], "fail")
        self.assertEqual(out["gh"][0], "ok")
        self.assertNotIn("pr_number", out)

    def test_unresolved_threads_on_an_open_pr(self):
        self.git("checkout", "-q", "-b", "feature/t")
        head = self.git("rev-parse", "HEAD")
        self.use_stub_gh(GH_STUB_PR_VIEW=f"3\tOPEN\tfalse\tAPPROVED\tpass\t{head}", GH_STUB_THREADS="2")
        self.assertEqual(self.run_script()["pr_unresolved_threads"][0], "2")

    def test_no_thread_query_on_a_merged_pr(self):
        self.git("checkout", "-q", "-b", "feature/m")
        head = self.git("rev-parse", "HEAD")
        self.use_stub_gh(GH_STUB_PR_VIEW=f"3\tMERGED\tfalse\tAPPROVED\tpass\t{head}")
        self.assertNotIn("pr_unresolved_threads", self.run_script())

    def test_merged_pr_list_only_when_a_branch_needs_it(self):
        log = self.tmp / "gh.log"
        self.use_stub_gh(GH_STUB_LOG=str(log))
        self.run_script()
        self.assertFalse(log.exists())
        self.git("branch", "feature/unmerged")
        self.git("checkout", "-q", "feature/unmerged")
        self.write("u.txt")
        self.commit("u")
        self.git("checkout", "-q", "main")
        self.run_script()
        self.assertEqual(log.read_text().split("\n")[0], "pr list")


class Finish(DodCheckCase):
    """--finish <topic>: switch, pull, delete local and remote, prune, then a fresh snapshot."""

    def steps(self, out):
        return {k: v[0] for k, v in out.items() if k.startswith("finish_")}

    def topic(self, name="feature/f", push=True):
        self.git("checkout", "-q", "-b", name)
        self.write(name.replace("/", "-") + ".txt")
        self.commit(name)
        if push:
            self.git("push", "-q", "-u", "origin", name)
        return self.git("rev-parse", "HEAD")

    def merge_on_remote(self, name):
        self.git("push", "-q", "origin", f"{name}:main")

    def test_ancestor_merge_closes_everything(self):
        self.topic()
        self.merge_on_remote("feature/f")
        done = subprocess.run([BASH, str(SCRIPT), "--finish", "feature/f"], cwd=self.repo, env=self.env,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        lines = [l for l in done.stdout.splitlines() if l.startswith("finish_step:")]
        self.assertEqual(lines, [
            "finish_step: clean OK",
            "finish_step: switch OK main",
            "finish_step: pull OK",
            "finish_step: delete_local OK via=ancestor",
            "finish_step: delete_remote OK",
            "finish_step: prune OK",
        ])
        out = parse(done.stdout)
        self.assertEqual(out["branch"][0], "main")
        self.assertEqual(out["fetch"][0], "skipped")
        self.assertEqual(out["merged_branches"][0], "0")
        self.assertEqual(self.git("ls-remote", "--heads", "origin", "feature/f"), "")

    def test_squash_merge_uses_force_delete(self):
        tip = self.topic(push=False)
        self.git("checkout", "-q", "main")
        self.write("squashed.txt")
        self.commit("squash")
        self.git("push", "-q", "origin", "main")
        self.use_stub_gh(GH_STUB_MERGED=f"feature/f\t{tip}")
        out = self.run_script("--finish", "feature/f")
        self.assertIn("finish_step", out)
        done = subprocess.run(["git", "rev-parse", "--verify", "--quiet", "refs/heads/feature/f"],
                              cwd=self.repo, env=self.env, capture_output=True, text=True)
        self.assertNotEqual(done.returncode, 0)

    def test_remote_tip_that_moved_is_kept(self):
        self.topic()
        self.merge_on_remote("feature/f")
        other = self.tmp / "other"
        self.git("clone", "-q", "-b", "feature/f", str(self.remote), str(other), cwd=self.tmp)
        self.write("more.txt", repo=other)
        self.git("add", "-A", cwd=other)
        self.git("commit", "-q", "-m", "more", cwd=other)
        self.git("push", "-q", "origin", "feature/f", cwd=other)
        done = subprocess.run([BASH, str(SCRIPT), "--finish", "feature/f"], cwd=self.repo, env=self.env,
                              capture_output=True, text=True)
        self.assertIn("finish_step: delete_remote SKIPPED remote tip differs from the deleted local tip",
                      done.stdout)
        self.assertNotEqual(self.git("ls-remote", "--heads", "origin", "feature/f"), "")

    def test_not_merged_deletes_nothing(self):
        self.topic()
        done = subprocess.run([BASH, str(SCRIPT), "--finish", "feature/f"], cwd=self.repo, env=self.env,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 1)
        self.assertIn("finish_step: delete_local FAILED not provably merged", done.stdout)
        self.git("rev-parse", "--verify", "refs/heads/feature/f")

    def test_dirty_tree_stops_before_switching(self):
        self.topic()
        self.merge_on_remote("feature/f")
        self.write("README.md", "dirty\n")
        done = subprocess.run([BASH, str(SCRIPT), "--finish", "feature/f"], cwd=self.repo, env=self.env,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 1)
        self.assertIn("finish_step: clean FAILED", done.stdout)
        self.assertEqual(self.git("branch", "--show-current"), "feature/f")

    def test_non_fast_forward_pull_stops(self):
        self.topic()
        self.merge_on_remote("feature/f")
        self.git("checkout", "-q", "main")
        self.write("local-only.txt")
        self.commit("diverge")
        self.git("checkout", "-q", "feature/f")
        done = subprocess.run([BASH, str(SCRIPT), "--finish", "feature/f"], cwd=self.repo, env=self.env,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 1)
        self.assertIn("finish_step: pull FAILED", done.stdout)
        self.git("rev-parse", "--verify", "refs/heads/feature/f")

    def test_integration_branch_is_refused(self):
        self.run_script("--finish", "main", expect=2)
        self.run_script("--finish", "no-such-branch", expect=2)


if __name__ == "__main__":
    unittest.main()
