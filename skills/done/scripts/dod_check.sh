#!/usr/bin/env bash
# Read-only snapshot of a work session's delivery state, for the `done` skill.
# Prints `key: value` lines; list items are indented below their key.
# The only thing it changes is remote-tracking refs, through `git fetch --prune`, except with --finish.
#
# Usage: dod_check.sh [--base <branch>] [--since <rev>] [--no-fetch] [--max-list <n>] [--finish <topic>]
#   --base <branch>   integration branch (default: the remote's default branch, else the first of
#                     dev, develop, main, master that exists); an unknown branch is a usage error
#   --since <rev>     the session's first commit's parent: its changes count as the session's work
#                     even when already pushed to the integration branch
#   --no-fetch        do not contact the remote
#   --max-list <n>    longest list printed in full (default 30)
#   --finish <topic>  close a merged topic branch: switch to the integration branch, pull --ff-only,
#                     delete <topic> locally (-d if an ancestor, -D if a merged pull request has its
#                     exact tip) and on the remote (only if its tip equals the local one), prune; one
#                     `finish_step: <step> OK|FAILED|SKIPPED [detail]` line per step, then a snapshot
#                     taken without fetching. Stops at the first failure.
# Environment: DOD_CHECK_GH names the GitHub CLI executable (default: gh).
# The remote is the current branch's upstream remote, else origin, else the first remote.
# Exit status: 0 snapshot printed, 1 a --finish step failed, 2 usage error. bash 3.2 and BSD tools.
set -u

BASE=""
SINCE=""
FETCH=1
MAX_LIST=30
FINISH=""
GH="${DOD_CHECK_GH:-gh}"
INTEGRATION_NAMES="dev develop main master"
TAB="$(printf '\t')"
SELF="$(cd "$(dirname "$0")" && pwd -P)/$(basename "$0")"

usage() { echo "usage: dod_check.sh [--base <branch>] [--since <rev>] [--no-fetch] [--max-list <n>] [--finish <topic>]" >&2; exit 2; }

while [ $# -gt 0 ]; do
    case "$1" in
        --base) [ $# -ge 2 ] || usage; BASE="$2"; shift 2 ;;
        --since) [ $# -ge 2 ] || usage; SINCE="$2"; shift 2 ;;
        --finish) [ $# -ge 2 ] || usage; FINISH="$2"; shift 2 ;;
        --no-fetch) FETCH=0; shift ;;
        --max-list)
            [ $# -ge 2 ] || usage
            case "$2" in ''|*[!0-9]*) usage ;; esac
            MAX_LIST="$2"; shift 2 ;;
        *) usage ;;
    esac
done

WORK="$(mktemp -d "${TMPDIR:-/tmp}/dod_check.XXXXXX")" || { echo "dod_check.sh: cannot create a temporary directory" >&2; exit 1; }
trap 'rm -rf "$WORK"' EXIT

g() { git -c core.quotepath=false "$@" 2>/dev/null; }
count() { wc -l < "$1" | tr -d ' '; }
has_ref() { g show-ref --verify --quiet "$1"; }

# Prints the lines of file $2 indented by $1, at most MAX_LIST of them.
print_list() {
    awk -v pad="$1" -v max="$MAX_LIST" '
        NR <= max { print pad $0 }
        END { if (NR > max) print pad "... (+" NR - max " more)" }
    ' "$2"
}

# Prints `key: <count>` and the lines of the file as list items.
print_counted() {
    echo "$1: $(count "$2")"
    print_list "  " "$2"
}

# Prints the DoD file names (any letter case) found in directory $1, one per line.
dod_names() {
    ls -1a "$1" 2>/dev/null | grep -i '^dod\.md$' | while IFS= read -r name; do
        [ -f "$1/$name" ] && echo "$name"
    done
}

# Reads changed paths from file $1 (relative to $ROOT) and prints the DoD files that govern them,
# most specific first, each with the number of changed paths it is the nearest file for.
report_dod_files() {
    local changed="$1" dir names
    : > "$WORK/map"; : > "$WORK/conflicts"
    # An entry ending in "/" is an untracked nested repository: it counts as one path and is not entered.
    # The root is always looked at, so its DoD file is reported even when nothing changed.
    awk '{ p = $0; sub(/\/$/, "", p); while (match(p, /\/[^\/]*$/)) { p = substr(p, 1, RSTART - 1); print p } }
         END { print "." }' "$changed" | LC_ALL=C sort -u > "$WORK/dirs"
    while IFS= read -r dir; do
        [ -d "$ROOT/$dir" ] || continue
        names="$(dod_names "$ROOT/$dir")"
        [ -n "$names" ] || continue
        printf '%s\t%s\n' "$dir" "$(printf '%s\n' "$names" | head -1)" >> "$WORK/map"
        [ "$(printf '%s\n' "$names" | wc -l | tr -d ' ')" -gt 1 ] && echo "$dir" >> "$WORK/conflicts"
    done < "$WORK/dirs"

    # nearest: "<dod file>\t<path>" for each path with a governing file; orphans: the other paths.
    awk -F'\t' -v orphans="$WORK/orphans" '
        NR == FNR { file[$1] = ($1 == "." ? $2 : $1 "/" $2); next }
        {
            p = $0; found = ""; sub(/\/$/, "", p)
            while (match(p, /\/[^\/]*$/)) { p = substr(p, 1, RSTART - 1); if (p in file) { found = file[p]; break } }
            if (found == "" && ("." in file)) found = file["."]
            if (found == "") print $0 > orphans; else print found "\t" $0
        }
    ' "$WORK/map" "$changed" > "$WORK/nearest"
    [ -f "$WORK/orphans" ] || : > "$WORK/orphans"

    # Most specific first: deeper directories before their ancestors.
    awk -F'\t' '{ f = ($1 == "." ? $2 : $1 "/" $2); n = gsub(/\//, "/", $1); if ($1 == ".") n = -1; print n "\t" f }' \
        "$WORK/map" | LC_ALL=C sort -t "$TAB" -k1,1nr -k2,2 | cut -f2- > "$WORK/dods"

    echo "dod_files: $(count "$WORK/dods")"
    while IFS= read -r dod; do
        echo "  $dod paths=$(awk -F'\t' -v d="$dod" '$1 == d' "$WORK/nearest" | wc -l | tr -d ' ')"
    done < "$WORK/dods"
    if [ -s "$WORK/orphans" ] && [ -s "$WORK/dods" ]; then print_counted no_dod_paths "$WORK/orphans"; fi
    if [ -s "$WORK/conflicts" ]; then print_counted dod_name_conflict "$WORK/conflicts"; fi
}

# Prints "ancestor" or "pr" when local branch $1 is provably merged, nothing otherwise.
# Needs BASE_REF; looks up merged pull requests (once) only for a branch that is not an ancestor.
merged_via() {
    local name="$1" tip
    if g merge-base --is-ancestor "refs/heads/$name" "$BASE_REF"; then echo ancestor; return; fi
    load_merged_prs
    tip="$(g rev-parse "refs/heads/$name")"
    grep -qxF "$name$TAB$tip" "$WORK/merged_prs" && echo pr
}

MERGED_PRS_LOADED=0
load_merged_prs() {
    [ "$MERGED_PRS_LOADED" -eq 1 ] && return
    MERGED_PRS_LOADED=1
    : > "$WORK/merged_prs"
    [ "$GH_STATE" = "ok" ] || return
    "$GH" pr list --state merged --limit 200 --json headRefName,headRefOid \
        --jq '.[] | [.headRefName, .headRefOid] | @tsv' > "$WORK/merged_prs" 2> "$WORK/gh_err" || gh_failed
}

gh_failed() { if grep -qiE 'auth|login|credential|token' "$WORK/gh_err"; then GH_STATE="unauthenticated"; else GH_STATE="error"; fi; }

# Prints the added lines of a unified diff (on stdin) that look like debug leftovers, as "path:line: text".
debug_lines() {
    awk '
        /^\+\+\+ / { path = substr($0, 5); sub(/^b\//, "", path); next }
        /^@@ / { split($3, a, ","); line = substr(a[1], 2) + 0; next }
        /^\+/ {
            text = substr($0, 2)
            if (text ~ /console\.log\(|debugger;|pdb\.set_trace|breakpoint\(\)|binding\.pry|var_dump\(|dbg!\(|FIXME|XXX|TODO/) {
                sub(/^[ \t]+/, "", text); print path ":" line ": " substr(text, 1, 120)
            }
            line++
        }
    '
}

# ---------------------------------------------------------------- outside git
if ! ROOT="$(g rev-parse --show-toplevel)" || [ -z "$ROOT" ]; then
    [ -z "$FINISH" ] || { echo "dod_check.sh: --finish needs a git repository" >&2; exit 2; }
    ROOT="$(pwd -P)"
    echo "git: no"
    echo "root: $ROOT"
    dod_names "$ROOT" > "$WORK/dods"
    print_counted dod_files "$WORK/dods"
    exit 0
fi
cd "$ROOT" || exit 1

# ---------------------------------------------------------------- branches and remote
BRANCH="$(g symbolic-ref --quiet --short HEAD)" || BRANCH=""
HAS_HEAD=1
g rev-parse --verify --quiet HEAD >/dev/null || HAS_HEAD=0

REMOTE=""
[ -n "$BRANCH" ] && REMOTE="$(g config --get "branch.$BRANCH.remote")"
if [ -z "$REMOTE" ] || [ "$REMOTE" = "." ]; then
    if g remote | grep -qxF origin; then REMOTE="origin"; else REMOTE="$(g remote | head -1)"; fi
fi

if [ -n "$SINCE" ] && ! g rev-parse --verify --quiet "$SINCE^{commit}" >/dev/null; then
    echo "dod_check.sh: --since: no commit named '$SINCE'" >&2
    exit 2
fi

if [ -z "$REMOTE" ] || [ "$FETCH" -eq 0 ]; then
    FETCH_STATE="skipped"
elif GIT_TERMINAL_PROMPT=0 git fetch --prune --quiet "$REMOTE" >/dev/null 2>&1; then
    FETCH_STATE="ok"
else
    FETCH_STATE="failed"
fi

INTEGRATION="$BASE"
[ -n "$REMOTE" ] && INTEGRATION="${INTEGRATION#"$REMOTE"/}"
if [ -n "$INTEGRATION" ] && ! has_ref "refs/heads/$INTEGRATION" && ! has_ref "refs/remotes/$REMOTE/$INTEGRATION"; then
    echo "dod_check.sh: --base: no branch named '$INTEGRATION'" >&2
    exit 2
fi
if [ -z "$INTEGRATION" ] && [ -n "$REMOTE" ]; then
    INTEGRATION="$(g symbolic-ref --quiet --short "refs/remotes/$REMOTE/HEAD")" && INTEGRATION="${INTEGRATION#"$REMOTE"/}"
fi
if [ -z "$INTEGRATION" ]; then
    for name in $INTEGRATION_NAMES; do
        if has_ref "refs/heads/$name" || has_ref "refs/remotes/$REMOTE/$name"; then INTEGRATION="$name"; break; fi
    done
fi

# The ref the session's work is compared with: the remote copy when there is one.
BASE_REF=""
if [ -n "$INTEGRATION" ]; then
    if has_ref "refs/remotes/$REMOTE/$INTEGRATION"; then BASE_REF="$REMOTE/$INTEGRATION"
    elif has_ref "refs/heads/$INTEGRATION"; then BASE_REF="$INTEGRATION"; fi
fi

URL=""
[ -n "$REMOTE" ] && URL="$(g config --get "remote.$REMOTE.url")"
case "$URL" in *github.com[:/]*) FORGE="github" ;; *) FORGE="unknown" ;; esac
GH_STATE="ok"
if [ "$FORGE" = "github" ] && ! command -v "$GH" >/dev/null 2>&1; then GH_STATE="missing"; fi
[ "$FORGE" = "github" ] || GH_STATE="none"

# ---------------------------------------------------------------- --finish
if [ -n "$FINISH" ]; then
    step() { echo "finish_step: $*"; }
    case " $INTEGRATION_NAMES $INTEGRATION " in *" $FINISH "*) echo "dod_check.sh: --finish: '$FINISH' is an integration branch" >&2; exit 2 ;; esac
    has_ref "refs/heads/$FINISH" || { echo "dod_check.sh: --finish: no local branch named '$FINISH'" >&2; exit 2; }
    [ -n "$BASE_REF" ] || { echo "dod_check.sh: --finish: no integration branch" >&2; exit 2; }
    RC=0
    TIP="$(g rev-parse "refs/heads/$FINISH")"
    REMOTE_TIP=""
    has_ref "refs/remotes/$REMOTE/$FINISH" && REMOTE_TIP="$(g rev-parse "refs/remotes/$REMOTE/$FINISH")"
    # Merged state comes from the fetched remote integration branch, which the pull below does not move.
    VIA="$(merged_via "$FINISH")"
    if [ -z "$VIA" ]; then
        step delete_local FAILED not provably merged; RC=1
    elif [ -n "$(g status --porcelain)" ]; then
        step clean FAILED uncommitted or untracked files; RC=1
    else
        step clean OK
        if [ "$BRANCH" = "$INTEGRATION" ]; then step switch SKIPPED already on "$INTEGRATION"
        elif g switch --quiet "$INTEGRATION"; then step switch OK "$INTEGRATION"
        else step switch FAILED "$INTEGRATION"; RC=1; fi
    fi
    if [ "$RC" -eq 0 ]; then
        if ! g rev-parse --verify --quiet '@{u}' >/dev/null; then step pull SKIPPED no upstream
        elif GIT_TERMINAL_PROMPT=0 git pull --ff-only --quiet >/dev/null 2>&1; then step pull OK
        else step pull FAILED not a fast-forward: merge or reset needed, not done; RC=1; fi
    fi
    if [ "$RC" -eq 0 ]; then
        if [ "$VIA" = "ancestor" ] && g branch --quiet -d "$FINISH"; then step delete_local OK via=ancestor
        elif [ "$VIA" = "pr" ] && g branch --quiet -D "$FINISH"; then step delete_local OK via=pr
        else step delete_local FAILED git branch refused, checked out in another worktree?; RC=1; fi
    fi
    if [ "$RC" -eq 0 ]; then
        if [ -z "$REMOTE_TIP" ]; then step delete_remote SKIPPED no remote branch
        elif [ "$REMOTE_TIP" != "$TIP" ]; then step delete_remote SKIPPED remote tip differs from the deleted local tip
        elif GIT_TERMINAL_PROMPT=0 git push --quiet "$REMOTE" --delete "$FINISH" >/dev/null 2>&1; then step delete_remote OK
        else step delete_remote FAILED push --delete refused; RC=1; fi
        if GIT_TERMINAL_PROMPT=0 git fetch --prune --quiet "$REMOTE" >/dev/null 2>&1; then step prune OK
        else step prune FAILED; RC=1; fi
    fi
    ARGS="--no-fetch --max-list $MAX_LIST"
    [ -n "$BASE" ] && ARGS="$ARGS --base $BASE"
    [ -n "$SINCE" ] && ARGS="$ARGS --since $SINCE"
    # shellcheck disable=SC2086
    DOD_CHECK_GH="$GH" bash "$SELF" $ARGS
    exit "$RC"
fi

# ---------------------------------------------------------------- forge: pull request or CI of HEAD
PR_LINE=""
CI_HEAD=""
THREADS=""
CHECKS_CLASS='if length == 0 then "none"
    elif any(.[]; (.conclusion // .state // "") | ascii_upcase | test("FAILURE|ERROR|CANCELLED|TIMED_OUT|ACTION_REQUIRED|STARTUP_FAILURE")) then "fail"
    elif any(.[]; ((.status // "COMPLETED") | ascii_upcase) != "COMPLETED" or ((.state // "") | test("PENDING|EXPECTED"))) then "pending"
    else "pass" end'
if [ "$GH_STATE" = "ok" ] && [ "$HAS_HEAD" -eq 1 ]; then
    if [ -n "$BRANCH" ] && [ "$BRANCH" != "$INTEGRATION" ]; then
        if PR_LINE="$("$GH" pr view --json number,state,isDraft,reviewDecision,statusCheckRollup,headRefOid \
                --jq "[.number, .state, .isDraft, (.reviewDecision // \"\"), ((.statusCheckRollup // []) | $CHECKS_CLASS), .headRefOid] | @tsv" 2> "$WORK/gh_err")"; then
            :
        elif grep -qi 'no pull requests found' "$WORK/gh_err"; then
            PR_LINE="none"
        else
            PR_LINE=""; gh_failed
        fi
        if [ "$(printf '%s' "$PR_LINE" | cut -f2)" = "OPEN" ]; then
            THREADS="$("$GH" api graphql -F owner='{owner}' -F name='{repo}' -F n="$(printf '%s' "$PR_LINE" | cut -f1)" \
                -f query='query($owner:String!,$name:String!,$n:Int!){repository(owner:$owner,name:$name){pullRequest(number:$n){reviewThreads(first:100){nodes{isResolved}}}}}' \
                --jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not)] | length' 2> "$WORK/gh_err")" \
                || { THREADS="unknown"; }
        fi
    else
        CI_HEAD="$("$GH" run list --commit "$(g rev-parse HEAD)" --json status,conclusion --jq "$CHECKS_CLASS" 2> "$WORK/gh_err")" \
            || { CI_HEAD=""; gh_failed; }
    fi
fi

# ---------------------------------------------------------------- merged local branches
# A branch counts as merged when it is an ancestor of the integration branch, or when a merged
# pull request has exactly its tip as head (squash and rebase merges). The current branch is
# listed too, marked current=yes; the integration branch and the well-known names never are.
: > "$WORK/merged"
if [ -n "$BASE_REF" ]; then
    g for-each-ref --format='%(refname:short)' refs/heads | while read -r name; do
        [ "$name" = "$INTEGRATION" ] && continue
        case " $INTEGRATION_NAMES " in *" $name "*) continue ;; esac
        echo "$name"
    done > "$WORK/candidates"
    while read -r name; do
        via="$(merged_via "$name")"
        [ -n "$via" ] || continue
        if has_ref "refs/remotes/$REMOTE/$name"; then remote="yes"; else remote="no"; fi
        if [ "$name" = "$BRANCH" ]; then echo "$name remote=$remote via=$via current=yes"; else echo "$name remote=$remote via=$via"; fi
    done < "$WORK/candidates" > "$WORK/merged"
fi

# ---------------------------------------------------------------- output
echo "git: yes"
echo "root: $ROOT"
echo "branch: ${BRANCH:-(detached)}"
if [ "$HAS_HEAD" -eq 1 ]; then echo "head_tree: $(g rev-parse 'HEAD^{tree}')"; else echo "head: none"; fi
echo "remote: ${REMOTE:-none}"
echo "fetch: $FETCH_STATE"
echo "integration_branch: ${INTEGRATION:-none}"

UPSTREAM="$(g rev-parse --abbrev-ref --symbolic-full-name '@{u}')" || UPSTREAM=""
echo "upstream: ${UPSTREAM:-none}"
if [ -n "$UPSTREAM" ]; then
    COUNTS="$(g rev-list --left-right --count "$UPSTREAM...HEAD")"
    echo "ahead: $(printf '%s' "$COUNTS" | cut -f2)"
    echo "behind: $(printf '%s' "$COUNTS" | cut -f1)"
fi
if [ -n "$INTEGRATION" ] && has_ref "refs/heads/$INTEGRATION" && has_ref "refs/remotes/$REMOTE/$INTEGRATION"; then
    echo "integration_behind: $(g rev-list --count "$INTEGRATION..$REMOTE/$INTEGRATION")"
else
    echo "integration_behind: unknown"
fi

if [ "$HAS_HEAD" -eq 1 ]; then g diff --no-renames --name-only HEAD > "$WORK/modified"; else g diff --cached --name-only > "$WORK/modified"; fi
g ls-files --others --exclude-standard > "$WORK/untracked"
print_counted modified "$WORK/modified"
print_counted untracked "$WORK/untracked"
echo "stashes: $(g stash list | wc -l | tr -d ' ')"
echo "extra_worktrees: $(( $(g worktree list --porcelain | grep -c '^worktree ') - 1 ))"

echo "forge: $FORGE"
if [ "$FORGE" = "github" ]; then
    echo "gh: $GH_STATE"
    [ -n "$CI_HEAD" ] && echo "ci_head: $CI_HEAD"
    if [ "$PR_LINE" = "none" ]; then
        echo "pr_number: none"
    elif [ -n "$PR_LINE" ]; then
        REVIEW="$(printf '%s' "$PR_LINE" | cut -f4)"
        echo "pr_number: $(printf '%s' "$PR_LINE" | cut -f1)"
        echo "pr_state: $(printf '%s' "$PR_LINE" | cut -f2)"
        echo "pr_draft: $(printf '%s' "$PR_LINE" | cut -f3)"
        echo "pr_review: ${REVIEW:-none}"
        echo "pr_checks: $(printf '%s' "$PR_LINE" | cut -f5)"
        # no: the pull request describes an earlier state of this branch, not the current HEAD.
        if [ "$(printf '%s' "$PR_LINE" | cut -f6)" = "$(g rev-parse HEAD)" ]; then echo "pr_head_matches: yes"; else echo "pr_head_matches: no"; fi
        [ -n "$THREADS" ] && echo "pr_unresolved_threads: $THREADS"
    fi
fi
print_counted merged_branches "$WORK/merged"

# ---------------------------------------------------------------- the session's work and its DoD files
MERGE_BASE=""
if [ -n "$BASE_REF" ] && [ "$HAS_HEAD" -eq 1 ]; then MERGE_BASE="$(g merge-base HEAD "$BASE_REF")"; fi
DIFF_BASE="${SINCE:-$MERGE_BASE}"
{
    [ -n "$MERGE_BASE" ] && g diff --no-renames --name-only "$MERGE_BASE" HEAD
    [ -n "$SINCE" ] && g diff --no-renames --name-only "$SINCE" HEAD
    cat "$WORK/modified" "$WORK/untracked"
} | LC_ALL=C sort -u > "$WORK/changed"
print_counted changed_paths "$WORK/changed"

{
    [ -n "$DIFF_BASE" ] && g diff --no-color --no-ext-diff -U0 "$DIFF_BASE"
    while IFS= read -r f; do
        case "$f" in */) continue ;; esac
        [ -f "$f" ] && awk -v p="$f" 'BEGIN { print "+++ b/" p; print "@@ -0,0 +1 @@" } { print "+" $0 }' "$f"
    done < "$WORK/untracked"
} | debug_lines > "$WORK/debug"
print_counted debug_markers "$WORK/debug"

report_dod_files "$WORK/changed"
exit 0
