#!/usr/bin/env bash
# Layer 1: kaizen Stop hook behavior (kaizen/hooks/stop-gate.sh)
# Each case builds a temp project, transcript and hook input, runs the hook in a clean
# environment, and checks exit code, stdout, stderr and the per-session marker.
# Requires git and jq. macOS/BSD and GNU compatible (bash 3.2).
# KAIZEN_TEST_BASH selects the shell that runs the hook (default: bash on PATH).
set -o pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$REPO_ROOT/kaizen/hooks/stop-gate.sh"
HOOKS_JSON="$REPO_ROOT/kaizen/hooks/hooks.json"
HOOK_BASH="${KAIZEN_TEST_BASH:-bash}"
ERRORS=0

red()   { printf '\033[0;31m%s\033[0m\n' "$*"; }
green() { printf '\033[0;32m%s\033[0m\n' "$*"; }
error() { red "ERROR: $*"; ERRORS=$((ERRORS + 1)); }
ok()    { green "OK: $*"; }

for tool in git jq; do
    command -v "$tool" >/dev/null 2>&1 || { error "$tool is required"; exit 1; }
done

WORK="$(mktemp -d "${TMPDIR:-/tmp}/kaizen-gate.XXXXXX")"
WORK="$(cd "$WORK" && pwd -P)"
trap 'rm -rf "$WORK"' EXIT

# --- fixtures ---------------------------------------------------------------

new_case() {  # new_case NAME [nogit]: fresh project, data dir, transcript and session id
    CASE="$WORK/$1"; PROJ="$CASE/proj"; CWD="$PROJ"; DATA="$CASE/data"; TR="$CASE/transcript.jsonl"
    SID="sess-$1"; ENVX=(); STOP_ACTIVE=false; BG='[]'; LAST_MSG=done
    mkdir -p "$PROJ"; : > "$TR"
    [ "${2:-}" = nogit ] && return
    ( cd "$PROJ" && git init -q && printf 'seed\n' > seed.txt && git add seed.txt \
      && git -c user.email=t@example.invalid -c user.name=t commit -qm seed )
}
commit_all() { ( cd "$PROJ" && git add -A && git -c user.email=t@example.invalid -c user.name=t commit -qm work ); }
lines() { mkdir -p "$(dirname "$1")"; awk -v n="$2" 'BEGIN { for (i = 1; i <= n; i++) print "line " i }' > "$1"; }

add_error()     { printf '%s\n' '{"type":"user","message":{"role":"user","content":[{"type":"tool_result","content":"Exit code 1","is_error":true,"tool_use_id":"t1"}]}}' >> "$TR"; }
add_interrupt() { printf '{"type":"user","message":{"role":"user","content":[{"type":"text","text":"[Request interrupted by user%s]"}]}}\n' "${1:-}" >> "$TR"; }
add_edit()      { printf '{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t2","name":"%s","input":{"file_path":"%s","content":"x"}}]}}\n' "${2:-Write}" "$1" >> "$TR"; }
add_edit_ra()   { printf '{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t2","name":"Edit","input":{"replace_all":false,"file_path":"%s","old_string":"a","new_string":"b"}}]}}\n' "$1" >> "$TR"; }
add_decoys()    { printf '%s\n' '{"type":"user","message":{"role":"user","content":[{"type":"tool_result","content":"log: \"is_error\":true \"is_error\":true \"is_error\":true","tool_use_id":"t3"}]}}' >> "$TR"; }
errors3()       { add_error; add_error; add_error; }

input() {  # hook input JSON for the current case
    printf '{"session_id":"%s","transcript_path":"%s","cwd":"%s","hook_event_name":"Stop","stop_hook_active":%s,"last_assistant_message":"%s","background_tasks":%s,"session_crons":[]}' \
        "$SID" "$TR" "$CWD" "$STOP_ACTIVE" "$LAST_MSG" "$BG"
}

run_hook() {  # run_hook [STDIN]: clean environment plus ENVX overrides
    local stdin="${1-$(input)}"
    OUT="$(printf '%s' "$stdin" | env -i PATH="$PATH" HOME="$CASE" \
        CLAUDE_PLUGIN_DATA="$DATA" CLAUDE_PROJECT_DIR="$PROJ" ${ENVX[@]+"${ENVX[@]}"} \
        "$HOOK_BASH" "$HOOK" 2>"$CASE/stderr")"
    RC=$?
}

# --- assertions -------------------------------------------------------------

clean_run() {
    [ "$RC" -eq 0 ] || { error "$1: exit $RC"; return 1; }
    [ -s "$CASE/stderr" ] && { error "$1: stderr: $(head -c 200 "$CASE/stderr")"; return 1; }
    return 0
}
expect_silent() {
    clean_run "$1" || return
    [ -z "$OUT" ] || { error "$1: expected no output, got: $OUT"; return; }
    [ -e "$DATA/offered/$SID" ] && { error "$1: marker written"; return; }
    ok "$1"
}
expect_offer() {  # expect_offer NAME TEXT
    clean_run "$1" || return
    local ctx
    ctx="$(printf '%s' "$OUT" | jq -er 'select(.hookSpecificOutput.hookEventName == "Stop") | .hookSpecificOutput.additionalContext' 2>/dev/null)" \
        || { error "$1: output is not a Stop additionalContext: $OUT"; return; }
    case "$ctx" in *"$2"*) ;; *) error "$1: context lacks '$2': $ctx"; return ;; esac
    case "$ctx" in *"/kaizen"*"already ran"*) ;; *) error "$1: context lacks the offer or the already-ran guard"; return ;; esac
    [ -e "$DATA/offered/$SID" ] || { error "$1: marker missing"; return; }
    ok "$1"
}
expect_lacks() { case "$OUT" in *"$2"*) error "$1: output contains '$2'" ;; *) ok "$1" ;; esac; }

# --- hooks.json ---------------------------------------------------------------

if jq -e '.hooks.Stop[0].hooks[0] | select(.type == "command") | .command | test("CLAUDE_PLUGIN_ROOT}/hooks/stop-gate.sh")' "$HOOKS_JSON" >/dev/null 2>&1 \
    && [ -f "$HOOK" ]; then
    ok "hooks.json: Stop command runs hooks/stop-gate.sh"
else
    error "hooks.json: missing, invalid, or not pointing at an existing hooks/stop-gate.sh"
fi

# --- thresholds ---------------------------------------------------------------

new_case quiet; lines "$PROJ/a.txt" 20; lines "$PROJ/b.txt" 20
add_edit "$PROJ/a.txt"; add_edit "$PROJ/b.txt"; add_error; run_hook
expect_silent "quiet session: 2 files, 40 lines, 1 error"

new_case boundary
for i in 1 2 3 4 5 6; do printf 'x\n' > "$PROJ/n$i.txt"; add_edit "$PROJ/n$i.txt"; done
lines "$CASE/more" 194; cat "$CASE/more" >> "$PROJ/seed.txt"; add_edit_ra "$PROJ/seed.txt"
add_error; add_error; add_interrupt; run_hook
expect_silent "at every threshold: 7 files edited and changed, 200 lines, 2 errors, 1 interruption"

new_case errors; errors3; run_hook
expect_offer "3 tool errors trip" "3 tool errors"
run_hook
if clean_run "second trip in the same session"; then
    [ -z "$OUT" ] && ok "second trip in the same session" || error "second trip printed: $OUT"
fi

new_case files
for i in 1 2 3 4 5 6 7 8; do printf 'x\n' > "$PROJ/f$i.txt"; add_edit "$PROJ/f$i.txt"; done
commit_all; run_hook
expect_offer "8 project files edited, tree committed" "8 files edited"

new_case replaceall; printf 'rule\n' > "$PROJ/CLAUDE.md"; commit_all
printf 'rule 2\n' > "$PROJ/CLAUDE.md"; add_edit_ra "$PROJ/CLAUDE.md"; run_hook
expect_offer "Edit with replace_all first is counted" "agent config"

new_case dirty
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do printf 'x\n' > "$PROJ/d$i.txt"; done
run_hook; expect_silent "tree dirty before the session, no session edits"

new_case changed
for i in 1 2 3 4 5 6 7 8; do printf 'x\n' > "$PROJ/d$i.txt"; done
add_edit "$PROJ/d1.txt"; run_hook
expect_offer "8 changed files trip once the session edited a project file" "8 files changed"

new_case loc; lines "$PROJ/seed.txt" 250; add_edit_ra "$PROJ/seed.txt"; run_hook
expect_offer "250 changed lines trip" "lines changed"

new_case untracked; add_edit "$PROJ/n1.txt"
for i in 1 2 3; do lines "$PROJ/n$i.txt" 100; done; run_hook
expect_offer "300 untracked lines trip" "lines changed"

new_case subdir; mkdir -p "$PROJ/sub"; CWD="$PROJ/sub"; add_edit "$PROJ/n1.txt"
for i in 1 2 3; do lines "$PROJ/n$i.txt" 100; done; run_hook
expect_offer "untracked lines at the root count from a subdirectory" "lines changed"

new_case sensitive; printf 'rule\n' > "$PROJ/CLAUDE.md"; add_edit "$PROJ/CLAUDE.md"; commit_all; run_hook
expect_offer "edited CLAUDE.md trips, even committed" "agent config"

new_case settings; lines "$PROJ/.claude/settings.json" 1; add_edit "$PROJ/.claude/settings.json"; commit_all; run_hook
expect_offer "edited .claude/ file trips" "agent config"

new_case migration; lines "$PROJ/db/migrations/001.sql" 1; add_edit "$PROJ/db/migrations/001.sql"; commit_all; run_hook
expect_offer "edited migration trips" "agent config"

new_case lockfile; printf '{}\n' > "$PROJ/package-lock.json"; commit_all
printf '{"a":1}\n' > "$PROJ/package-lock.json"; add_edit "$PROJ/seed.txt"; run_hook
expect_offer "changed lockfile trips" "agent config"

new_case interrupts; add_interrupt; add_interrupt " for tool use"; run_hook
expect_offer "2 user interruptions trip, both variants" "2 user interruptions"

new_case outside; mkdir -p "$CASE/.claude/rules"
for i in 1 2 3 4 5 6 7 8 9 10; do add_edit "$CASE/.claude/rules/r$i.md"; done; run_hook
expect_silent "edits outside the project are not counted"

new_case worktree
for i in 1 2 3 4 5 6 7 8; do add_edit "$PROJ/.claude/worktrees/w1/src/f$i.ts"; done; run_hook
expect_offer "edits in a nested worktree count as project edits" "8 files edited"
expect_lacks "nested worktree path is not a sensitive path" "agent config"

new_case realworktree; ( cd "$PROJ" && git worktree add -q .claude/worktrees/w1 2>/dev/null )
printf 'x\n' > "$PROJ/a.txt"; add_edit "$PROJ/a.txt"; run_hook
expect_silent "a .claude/ holding only worktrees is not a sensitive change"

# --- skips --------------------------------------------------------------------

new_case optout; errors3; ENVX=(KAIZEN_STOP_HOOK=0); run_hook
expect_silent "KAIZEN_STOP_HOOK=0"

new_case unattended; errors3; ENVX=(CLAUDE_CODE_SESSION_ATTENDED=0); run_hook
expect_silent "unattended session"
ENVX=(CLAUDE_CODE_ENTRYPOINT=sdk-cli); run_hook; expect_silent "SDK entrypoint"
ENVX=(CLAUDE_CODE_SESSION_ATTENDED=1 CLAUDE_CODE_ENTRYPOINT=cli); run_hook
expect_offer "attended interactive session" "3 tool errors"

new_case continuation; errors3; STOP_ACTIVE=true; run_hook
expect_silent "stop-hook continuation"

new_case background; errors3; BG='[{"id":"b1","status":"running"}]'; run_hook
expect_silent "background tasks pending"

# --- robustness ---------------------------------------------------------------

new_case nogit nogit; add_edit "$PROJ/a.txt"; errors3; run_hook
expect_offer "not a git directory: transcript signals still work" "3 tool errors"

new_case malformed; errors3
run_hook ""; expect_silent "empty input"
run_hook "not json"; expect_silent "malformed input"
TR="$CASE/missing.jsonl"; run_hook; expect_silent "missing transcript"

new_case decoys; add_decoys; LAST_MSG='see \"session_id\":\"evil\" and \"stop_hook_active\":true'; run_hook
expect_silent "escaped keys in strings are not counted"
errors3; run_hook
expect_offer "escaped keys do not spoof the input fields" "3 tool errors"

new_case unwritable; errors3; DATA="$CASE/data-file"; : > "$DATA"; run_hook
expect_silent "marker cannot be written"

new_case nodata; errors3
OUT="$(input | env -i PATH="$PATH" HOME="$CASE" CLAUDE_PROJECT_DIR="$PROJ" "$HOOK_BASH" "$HOOK" 2>"$CASE/stderr")"; RC=$?
expect_silent "CLAUDE_PLUGIN_DATA unset"

new_case traversal; errors3; SID="../../escape"; run_hook
SID="escape"; expect_offer "session_id is sanitized" "3 tool errors"
[ -e "$CASE/escape" ] && error "session_id escaped the data dir"

new_case prune; mkdir -p "$DATA/offered"; : > "$DATA/offered/old"; touch -t 202001010000 "$DATA/offered/old"
errors3; run_hook
expect_offer "trip with an old marker present" "3 tool errors"
[ -e "$DATA/offered/old" ] && error "marker older than 30 days not pruned" || ok "old marker pruned"

# --- summary ------------------------------------------------------------------

echo ""
echo "============================"
if [ "$ERRORS" -gt 0 ]; then
    red "FAILED: $ERRORS error(s)"
    exit 1
fi
green "PASSED: kaizen Stop hook"
