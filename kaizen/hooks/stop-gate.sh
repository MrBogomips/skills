#!/usr/bin/env bash
# kaizen Stop hook: once per session, when this session's mechanical signals cross the
# kaizen gate, ask the model to judge the full gate and offer /kaizen in one line.
# Never blocks, never calls a model, prints nothing on any failure, always exits 0.
# bash 3.2 and BSD/GNU tools; no jq or python.
exec 2>/dev/null

MAX_FILES=7 MAX_LOC=200 MIN_ERRORS=3 MIN_INTERRUPTS=2
SENSITIVE='(^|/)(\.claude/|CLAUDE(\.local)?\.md$|migrations?/)|(package-lock\.json|npm-shrinkwrap\.json|yarn\.lock|pnpm-lock\.yaml|\.lock|go\.sum)$'

[ "${KAIZEN_STOP_HOOK:-1}" = 0 ] && exit 0
[ "${CLAUDE_CODE_SESSION_ATTENDED:-1}" = 0 ] && exit 0
case "${CLAUDE_CODE_ENTRYPOINT:-}" in sdk*) exit 0 ;; esac

input="$(cat)"
has()   { printf '%s' "$input" | grep -qE "$1"; }
field() { printf '%s' "$input" | grep -oE "\"$1\" *: *\"[^\"]*\"" | head -n 1 | sed -E 's/^[^:]*: *"//; s/"$//'; }
gt()    { [ "${1:-0}" -gt "$2" ]; }

# Inside a JSON string every quote is escaped, so these matches are real top-level keys.
has '"stop_hook_active" *: *true' && exit 0
has '"background_tasks" *: *\[ *[^] ]' && exit 0
sid="$(field session_id | tr -cd 'A-Za-z0-9_-')"
[ -n "$sid" ] && [ -n "${CLAUDE_PLUGIN_DATA:-}" ] || exit 0
marker_dir="$CLAUDE_PLUGIN_DATA/offered"
[ -e "$marker_dir/$sid" ] && exit 0
tp="$(field transcript_path)"
cwd="$(field cwd)"
root="${CLAUDE_PROJECT_DIR:-$cwd}"

# Transcript signals. Edited paths are made relative to the project root; a nested
# worktree prefix is dropped so its files count as project files, not as .claude/.
errors=0 interrupts=0 files=0 sensitive=0
if [ -n "$tp" ] && [ -r "$tp" ]; then
    errors="$(grep -c '"is_error":true' "$tp")"
    interrupts="$(grep -c '"text":"\[Request interrupted by user' "$tp")"
    edited="$(grep -oE '"name":"(Edit|MultiEdit|Write|NotebookEdit)","input":\{[^}]*"(file|notebook)_path":"[^"]*"' "$tp" \
        | sed -E 's/.*_path":"//; s/"$//' \
        | awk -v r="$root/" 'r != "/" && index($0, r) == 1 { p = substr($0, length(r) + 1); sub(/^\.claude\/worktrees\/[^\/]+\//, "", p); print p }' \
        | sort -u)"
    files="$(printf '%s\n' "$edited" | grep -c .)"
    sensitive="$(printf '%s\n' "$edited" | grep -cE "$SENSITIVE")"
fi

# Working-tree signals, only for sessions that edited project files.
changed=0 loc=0
top=""
gt "$files" 0 && [ -d "$cwd" ] && top="$(git -C "$cwd" rev-parse --show-toplevel)"
if [ -n "$top" ]; then
    g() { git --no-optional-locks -C "$top" "$@"; }
    status="$(g status --porcelain -- . ':(exclude).claude/worktrees' | cut -c4-)"
    changed="$(printf '%s\n' "$status" | grep -c .)"
    sensitive=$((sensitive + $(printf '%s\n' "$status" | grep -cE "$SENSITIVE")))
    loc="$(g diff HEAD --shortstat | awk '{ for (i = 1; i < NF; i++) if ($(i + 1) ~ /^(insertion|deletion)/) s += $i } END { print s + 0 }')"
    new="$(cd "$top" && g ls-files -o --exclude-standard -z | xargs -0 cat | head -c 1000000 | wc -l)"
    loc=$((loc + new))
fi

r=""
gt "$files" "$MAX_FILES"                   && r="$r, $files files edited"
gt "$changed" "$MAX_FILES"                 && r="$r, $changed files changed"
gt "$loc" "$MAX_LOC"                       && r="$r, $loc lines changed"
gt "$sensitive" 0                          && r="$r, agent config, lockfile or migration changed"
gt "$errors" $((MIN_ERRORS - 1))           && r="$r, $errors tool errors"
gt "$interrupts" $((MIN_INTERRUPTS - 1))   && r="$r, $interrupts user interruptions"
[ -n "$r" ] || exit 0

# Record the offer first: if the marker cannot be written, stay silent rather than repeat.
mkdir -p "$marker_dir" && : > "$marker_dir/$sid" || exit 0
find "$marker_dir" -type f -mtime +30 -exec rm -f {} +
printf '{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"kaizen pre-check: %s. Judge the kaizen gate for this session: breadth of changes, errors, reworks and ambiguities you noticed. If it trips, end your reply with one line offering /kaizen before the session closes; otherwise, or if kaizen already ran in this session, add nothing about kaizen."}}\n' "${r#, }"
exit 0
