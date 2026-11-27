#!/usr/bin/env python3
"""Reads pull requests from GitHub with gh and classifies each into one state. Read-only.

Usage: python3 pr_status.py <owner/repo#N | pull request URL | #N> ...
A bare #N is a pull request of the repository in the current directory.
Prints a JSON array on stdout, one object per argument, in the order given. Python 3.8+, no dependencies.
Exit status: 0 every pull request was read, 1 at least one was not, 2 usage error, 3 gh is not installed.
"""
import json
import re
import shutil
import subprocess
import sys
import time

# One emoji per state. pick_state() returns the first state that applies, in this order.
EMOJI = {
    "merged": "✅",              # white heavy check mark
    "closed": "\U0001F5D1️",    # wastebasket: closed without merging
    "blocked": "⛔",             # no entry: conflict or changes requested
    "ci_failed": "❌",           # cross mark: at least one failed check
    "draft": "\U0001F4DD",           # memo
    "unreviewed": "\U0001F195",      # NEW button: open, no review by a person yet
    "in_progress": "\U0001F504",     # arrows: review, checks or merge under way
    "error": "⚠️",         # warning sign: the pull request could not be read
}
FAILED = {"FAILURE", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE"}
PASSED = {"SUCCESS", "NEUTRAL", "SKIPPED"}
IGNORED = {"STALE"}                 # an outdated run says nothing about the current commit
SUBMITTED_REVIEWS = {"APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED"}  # PENDING is an unsent draft
GH_TIMEOUT_SECONDS = 30
UNKNOWN_READS = 3                   # GitHub computes mergeability in the background after a push or a merge
UNKNOWN_WAIT_SECONDS = 2
EXIT_OK, EXIT_UNREAD, EXIT_USAGE, EXIT_NO_GH = 0, 1, 2, 3
REF_PATTERNS = (
    re.compile(r"^(?P<repo>[\w.-]+/[\w.-]+)#(?P<number>\d+)$"),
    re.compile(r"^https://github\.com/(?P<repo>[\w.-]+/[\w.-]+)/pull/(?P<number>\d+)(?:[/?#].*)?$"),
    re.compile(r"^#?(?P<number>\d+)$"),
)
# The first 100 reviews and checks are read; a pull request with more is classified on those.
QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { name }
    pullRequest(number: $number) {
      number url title state isDraft mergeable mergeStateStatus reviewDecision baseRefName
      author { login }
      reviews(first: 100) { nodes { state author { __typename login } } }
      commits(last: 1) { nodes { commit { statusCheckRollup { contexts(first: 100) { nodes {
        __typename
        ... on CheckRun { name status conclusion startedAt checkSuite { workflowRun { workflow { name } } } }
        ... on StatusContext { context state createdAt }
      } } } } } }
    }
  }
}
"""


class GhError(Exception):
    """gh failed or answered something unreadable."""


def parse_ref(ref):
    """Returns (owner/repo or None for the current repository, number). Raises ValueError otherwise."""
    for pattern in REF_PATTERNS:
        match = pattern.match(ref.strip())
        if match and int(match.group("number")) > 0:
            return match.groupdict().get("repo"), int(match.group("number"))
    raise ValueError(f"not a pull request reference: {ref!r} (use owner/repo#N, a pull request URL or #N)")


def run_gh(args):
    """Runs gh and returns stdout only: gh prints hints and upgrade notices on stderr."""
    try:
        done = subprocess.run(args, capture_output=True, text=True, timeout=GH_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        raise GhError(f"gh did not answer within {GH_TIMEOUT_SECONDS} seconds")
    except OSError as error:
        raise GhError(f"gh could not be run: {error}")
    if done.returncode != 0:
        raise GhError(done.stderr.strip().splitlines()[0] if done.stderr.strip() else "gh failed")
    return done.stdout


def read_json(run, args):
    try:
        return json.loads(run(args))
    except ValueError as error:
        raise GhError(f"unreadable answer from gh: {error}")


def current_repo(run=run_gh):
    """The repository of the current directory, for a bare #N."""
    name = read_json(run, ["gh", "repo", "view", "--json", "nameWithOwner"]).get("nameWithOwner")
    if not name:
        raise GhError("the current directory is not a GitHub repository: use owner/repo#N")
    return name


def normalize_check(node):
    if node.get("__typename") == "StatusContext":
        return {"context": node.get("context"), "state": node.get("state"), "startedAt": node.get("createdAt")}
    workflow = ((node.get("checkSuite") or {}).get("workflowRun") or {}).get("workflow") or {}
    return {"name": node.get("name"), "status": node.get("status"), "conclusion": node.get("conclusion"),
            "startedAt": node.get("startedAt"), "workflowName": workflow.get("name")}


def normalize(answer):
    """Flattens the GraphQL answer into the dictionary classify() reads."""
    repository = (answer.get("data") or {}).get("repository") or {}
    node = repository.get("pullRequest")
    if not node:
        errors = answer.get("errors") or [{}]
        raise GhError(errors[0].get("message") or "pull request not found")
    commits = (node.get("commits") or {}).get("nodes") or [{}]
    rollup = (commits[-1].get("commit") or {}).get("statusCheckRollup") or {}
    data = {key: value for key, value in node.items() if key not in ("reviews", "commits")}
    data["defaultBranch"] = (repository.get("defaultBranchRef") or {}).get("name")
    data["reviews"] = (node.get("reviews") or {}).get("nodes") or []
    data["statusCheckRollup"] = [normalize_check(c) for c in (rollup.get("contexts") or {}).get("nodes") or []]
    return data


def fetch(repo, number, run=run_gh, sleep=time.sleep):
    """Reads one pull request, again while an open one has no merge state yet."""
    owner, name = repo.split("/", 1)
    args = ["gh", "api", "graphql", "-f", f"query={QUERY}", "-F", f"owner={owner}", "-F", f"name={name}",
            "-F", f"number={number}"]
    for attempt in range(UNKNOWN_READS):
        data = normalize(read_json(run, args))
        if data.get("state") != "OPEN" or data.get("mergeable") != "UNKNOWN":
            break
        if attempt < UNKNOWN_READS - 1:
            sleep(UNKNOWN_WAIT_SECONDS)
    return data


def check_outcome(check):
    """CheckRun has status and conclusion; StatusContext has only state."""
    if check.get("state"):
        return check["state"]
    return check.get("conclusion") if check.get("status") == "COMPLETED" else "PENDING"


def latest_checks(checks):
    """A re-run leaves the earlier runs of the same check in the list: keep the newest of each."""
    latest = {}
    for position, check in enumerate(checks):
        key = (check.get("name") or check.get("context"), check.get("workflowName"))
        order = (check.get("startedAt") or "", position)
        if key not in latest or order > latest[key][0]:
            latest[key] = (order, check)
    return [check for _, check in latest.values()]


def check_names(checks, wanted):
    return sorted({c.get("name") or c.get("context") or "?" for c in checks if wanted(check_outcome(c))})


def count_reviews(data):
    """Reviews by people other than the author, and reviews by bots. Unsent drafts are not counted."""
    author = (data.get("author") or {}).get("login")
    people = bots = 0
    for review in data.get("reviews") or []:
        reviewer = review.get("author") or {}
        if review.get("state") not in SUBMITTED_REVIEWS or not reviewer.get("login"):
            continue
        if reviewer.get("__typename") == "Bot" or reviewer["login"].endswith("[bot]"):
            bots += 1
        elif reviewer["login"] != author:  # the author's replies to review comments come back as reviews
            people += 1
    return people, bots


def repo_of(url):
    match = re.match(r"^https://[^/]+/([^/]+/[^/]+)/pull/\d+", url or "")
    return match.group(1) if match else ""


def pick_state(data, facts):
    if data.get("state") == "MERGED":
        return "merged"
    if data.get("state") == "CLOSED":
        return "closed"
    if facts["conflict"] or facts["changes_requested"]:
        return "blocked"
    if facts["failed_checks"]:
        return "ci_failed"
    if facts["draft"]:
        return "draft"
    if facts["reviews"] == 0:
        return "unreviewed"
    return "in_progress"


def classify(data):
    """Turns one pull request into one state and the facts the status words are written from."""
    checks = latest_checks(data.get("statusCheckRollup") or [])
    merge_state = data.get("mergeStateStatus")
    people, bots = count_reviews(data)
    facts = {
        "repo": repo_of(data.get("url")),
        "number": data.get("number"),
        "url": data.get("url"),
        "title": data.get("title"),
        "base": data.get("baseRefName"),
        "default_branch": data.get("defaultBranch"),
        "base_is_default": data.get("baseRefName") == data.get("defaultBranch"),
        "draft": bool(data.get("isDraft")),
        "conflict": data.get("mergeable") == "CONFLICTING" or merge_state == "DIRTY",
        "changes_requested": data.get("reviewDecision") == "CHANGES_REQUESTED",
        "approved": data.get("reviewDecision") == "APPROVED",
        "reviews": people,
        "bot_reviews": bots,
        "failed_checks": check_names(checks, lambda outcome: outcome in FAILED),
        "pending_checks": check_names(checks, lambda outcome: outcome not in FAILED | PASSED | IGNORED),
        # UNSTABLE: mergeable although a check failed, so that check is not a required one.
        "failed_checks_not_required": merge_state == "UNSTABLE",
        "merge_state_unknown": data.get("state") == "OPEN" and data.get("mergeable") == "UNKNOWN",
    }
    state = pick_state(data, facts)
    return {"state": state, "emoji": EMOJI[state], **facts}


def collect(refs, run=run_gh, sleep=time.sleep):
    """One entry per reference, in order. A reference that cannot be read becomes an error entry."""
    entries, here = [], None
    for ref in refs:
        try:
            repo, number = parse_ref(ref)
            if repo is None:
                here = here or current_repo(run)
                repo, ref = here, f"{here}#{number}"
            entries.append({"ref": ref, **classify(fetch(repo, number, run=run, sleep=sleep))})
        except (ValueError, GhError) as error:
            entries.append({"ref": ref, "state": "error", "emoji": EMOJI["error"], "error": str(error)})
    return entries


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip(), file=sys.stderr)
        return EXIT_USAGE
    if not shutil.which("gh"):
        print("gh (the GitHub CLI) is not on the PATH: install it and run `gh auth login`.", file=sys.stderr)
        return EXIT_NO_GH
    entries = collect(argv)
    json.dump(entries, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return EXIT_UNREAD if any(entry["state"] == "error" for entry in entries) else EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
