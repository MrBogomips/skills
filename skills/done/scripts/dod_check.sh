#!/usr/bin/env bash
# Read-only snapshot of a work session's delivery state, for the `done` skill.
# Prints `key: value` lines; list items are indented below their key.
# The only thing it changes is remote-tracking refs, through `git fetch --prune`.
#
# Usage: dod_check.sh [--base <branch>] [--no-fetch] [--max-list <n>]
#   --base <branch>   integration branch (default: the remote's default branch, else the first of
#                     dev, develop, main, master that exists); an unknown branch is a usage error
#   --no-fetch        do not contact the remote
#   --max-list <n>    longest list printed in full (default 200)
# Environment: DOD_CHECK_GH names the GitHub CLI executable (default: gh).
# The remote is the current branch's upstream remote, else origin, else the first remote.
# Exit status: 0 snapshot printed, 2 usage error. bash 3.2 and BSD tools compatible.
set -u

BASE=""
FETCH=1
MAX_LIST=200
GH="${DOD_CHECK_GH:-gh}"
INTEGRATION_NAMES="dev develop main master"
TAB="$(printf '\t')"

usage() { echo "usage: dod_check.sh [--base <branch>] [--no-fetch] [--max-list <n>]" >&2; exit 2; }

while [ $# -gt 0 ]; do
    case "$1" in
        --base) [ $# -ge 2 ] || usage; BASE="$2"; shift 2 ;;
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

# Reads changed paths from file $1 (relative to $ROOT) and prints which DoD files govern them.
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
        echo "  $dod"
        awk -F'\t' -v d="$dod" '$1 == d { print $2 }' "$WORK/nearest" > "$WORK/paths"
        print_list "    " "$WORK/paths"
    done < "$WORK/dods"
    if [ -s "$WORK/orphans" ] && [ -s "$WORK/dods" ]; then print_counted no_dod_paths "$WORK/orphans"; fi
    if [ -s "$WORK/conflicts" ]; then print_counted dod_name_conflict "$WORK/conflicts"; fi
}

# ---------------------------------------------------------------- outside git
if ! ROOT="$(g rev-parse --show-toplevel)" || [ -z "$ROOT" ]; then
    ROOT="$(pwd -P)"
    echo "git: no"
    echo "root: $ROOT"
    dod_names "$ROOT" > "$WORK/dods"
    print_counted dod_files "$WORK/dods"
    exit 0
fi
cd "$ROOT" || exit 1
echo "git: yes"
echo "root: $ROOT"

# ---------------------------------------------------------------- branches
BRANCH="$(g symbolic-ref --quiet --short HEAD)" || BRANCH=""
echo "branch: ${BRANCH:-(detached)}"
HAS_HEAD=1
g rev-parse --verify --quiet HEAD >/dev/null || { HAS_HEAD=0; echo "head: none"; }

REMOTE=""
[ -n "$BRANCH" ] && REMOTE="$(g config --get "branch.$BRANCH.remote")"
if [ -z "$REMOTE" ] || [ "$REMOTE" = "." ]; then
    if g remote | grep -qxF origin; then REMOTE="origin"; else REMOTE="$(g remote | head -1)"; fi
fi
echo "remote: ${REMOTE:-none}"

if [ -z "$REMOTE" ] || [ "$FETCH" -eq 0 ]; then
    echo "fetch: skipped"
elif GIT_TERMINAL_PROMPT=0 git fetch --prune --quiet "$REMOTE" >/dev/null 2>&1; then
    echo "fetch: ok"
else
    echo "fetch: failed"
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
echo "integration_branch: ${INTEGRATION:-none}"

# The ref the session's work is compared with: the remote copy when there is one.
BASE_REF=""
if [ -n "$INTEGRATION" ]; then
    if has_ref "refs/remotes/$REMOTE/$INTEGRATION"; then BASE_REF="$REMOTE/$INTEGRATION"
    elif has_ref "refs/heads/$INTEGRATION"; then BASE_REF="$INTEGRATION"; fi
fi

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

# ---------------------------------------------------------------- working tree
if [ "$HAS_HEAD" -eq 1 ]; then g diff --no-renames --name-only HEAD > "$WORK/modified"; else g diff --cached --name-only > "$WORK/modified"; fi
g ls-files --others --exclude-standard > "$WORK/untracked"
print_counted modified "$WORK/modified"
print_counted untracked "$WORK/untracked"
echo "stashes: $(g stash list | wc -l | tr -d ' ')"
echo "extra_worktrees: $(( $(g worktree list --porcelain | grep -c '^worktree ') - 1 ))"

# ---------------------------------------------------------------- forge and pull request
URL=""
[ -n "$REMOTE" ] && URL="$(g config --get "remote.$REMOTE.url")"
case "$URL" in *github.com[:/]*) FORGE="github" ;; *) FORGE="unknown" ;; esac
echo "forge: $FORGE"

: > "$WORK/merged_prs"
if [ "$FORGE" = "github" ]; then
    GH_STATE="ok"
    PR_LINE=""
    gh_failed() { if grep -qiE 'auth|login|credential|token' "$1"; then GH_STATE="unauthenticated"; else GH_STATE="error"; fi; }
    if ! command -v "$GH" >/dev/null 2>&1; then
        GH_STATE="missing"
    else
        "$GH" pr list --state merged --limit 200 --json headRefName,headRefOid \
            --jq '.[] | [.headRefName, .headRefOid] | @tsv' > "$WORK/merged_prs" 2> "$WORK/gh_err" || gh_failed "$WORK/gh_err"
        if [ "$GH_STATE" = "ok" ] && [ -n "$BRANCH" ] && [ "$BRANCH" != "$INTEGRATION" ]; then
            CHECKS='(.statusCheckRollup // []) as $c
                | if ($c | length) == 0 then "none"
                  elif any($c[]; (.conclusion // .state // "") | test("FAILURE|ERROR|CANCELLED|TIMED_OUT|ACTION_REQUIRED|STARTUP_FAILURE")) then "fail"
                  elif any($c[]; ((.status // "COMPLETED") != "COMPLETED") or ((.state // "") | test("PENDING|EXPECTED"))) then "pending"
                  else "pass" end'
            if PR_LINE="$("$GH" pr view --json number,state,isDraft,reviewDecision,statusCheckRollup,headRefOid \
                    --jq "[.number, .state, .isDraft, (.reviewDecision // \"\"), ($CHECKS), .headRefOid] | @tsv" 2> "$WORK/gh_err")"; then
                :
            elif grep -qi 'no pull requests found' "$WORK/gh_err"; then
                PR_LINE="none"
            else
                PR_LINE=""; gh_failed "$WORK/gh_err"
            fi
        fi
    fi
    echo "gh: $GH_STATE"
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
    fi
fi

# ---------------------------------------------------------------- merged local branches
# A branch counts as merged when it is an ancestor of the integration branch, or when a merged
# pull request has exactly its tip as head (squash and rebase merges). The current branch is
# listed too, marked current=yes; the integration branch and the well-known names never are.
: > "$WORK/merged"
if [ -n "$BASE_REF" ]; then
    g for-each-ref --format='%(refname:short)' --merged "$BASE_REF" refs/heads > "$WORK/ancestors"
    g for-each-ref --format='%(refname:short) %(objectname)' refs/heads | while read -r name tip; do
        [ "$name" = "$INTEGRATION" ] && continue
        case " $INTEGRATION_NAMES " in *" $name "*) continue ;; esac
        if grep -qxF "$name" "$WORK/ancestors"; then via="ancestor"
        elif grep -qxF "$name$TAB$tip" "$WORK/merged_prs"; then via="pr"
        else continue; fi
        if has_ref "refs/remotes/$REMOTE/$name"; then remote="yes"; else remote="no"; fi
        if [ "$name" = "$BRANCH" ]; then echo "$name remote=$remote via=$via current=yes"; else echo "$name remote=$remote via=$via"; fi
    done > "$WORK/merged"
fi
print_counted merged_branches "$WORK/merged"

# ---------------------------------------------------------------- the session's work and its DoD files
{
    if [ -n "$BASE_REF" ] && [ "$HAS_HEAD" -eq 1 ]; then
        MERGE_BASE="$(g merge-base HEAD "$BASE_REF")" && g diff --no-renames --name-only "$MERGE_BASE" HEAD
    fi
    cat "$WORK/modified" "$WORK/untracked"
} | LC_ALL=C sort -u > "$WORK/changed"
print_counted changed_paths "$WORK/changed"
report_dod_files "$WORK/changed"
exit 0
