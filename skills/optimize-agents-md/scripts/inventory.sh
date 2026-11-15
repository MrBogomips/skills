#!/bin/bash
# Inventory of a project's agent instruction files, read-only.
# Usage: bash inventory.sh [project-root]   (default: the current directory)
# Prints "key: value" lines; keys may repeat (file, rule, import, nested, skill, skill-candidate, startup, warn).
# Startup sizes assume a session launched at the project root. Bash 3.2 and BSD tools.

set -u

LINE_TARGET=200          # Claude Code docs: "target under 200 lines per CLAUDE.md file"
CODEX_MAX_BYTES=32768    # Codex project_doc_max_bytes default (32 KiB, all AGENTS.md files together)
PRUNE_DIRS=".git node_modules vendor dist build .venv venv target .next .cache"

root="${1:-.}"
if [ ! -d "$root" ]; then
    echo "error: not a directory: $root" >&2
    exit 2
fi
root="$(cd "$root" && pwd -P)"
cd "$root" || exit 2

count_lines() { awk 'END { print NR }' "$1"; }
count_bytes() { wc -c < "$1" | tr -d ' '; }

# Identity of a file through symlinks (its inode), for "same file" tests without readlink -f.
file_id() { ls -iLd "$1" 2>/dev/null | awk '{ print $1 }'; }
same_file() { [ -e "$1" ] && [ -e "$2" ] && [ "$(file_id "$1")" = "$(file_id "$2")" ]; }

# Running totals per harness. Claude Code counts each physical file once (a file may be both loaded and imported).
claude_lines=0; claude_bytes=0; codex_lines=0; codex_bytes=0
claude_counted=" "
add_claude() {
    local id
    id="$(file_id "$1")"
    case "$claude_counted" in *" $id "*) return 0 ;; esac
    claude_counted="$claude_counted$id "
    claude_lines=$((claude_lines + $(count_lines "$1"))); claude_bytes=$((claude_bytes + $(count_bytes "$1")))
}
add_codex()  { codex_lines=$((codex_lines + $(count_lines "$1")));   codex_bytes=$((codex_bytes + $(count_bytes "$1"))); }

warn_if_long() {
    local n
    n=$(count_lines "$1")
    if [ "$n" -gt "$LINE_TARGET" ]; then
        echo "warn: $1 has $n lines, over the $LINE_TARGET-line target"
    fi
}

# --- git and harness signals ---
if git -C "$root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then echo "git: yes"; else echo "git: no"; fi

signals=""
{ [ -e CLAUDE.md ] || [ -d .claude ] || [ -e CLAUDE.local.md ]; } && signals="$signals claude"
{ [ -d .codex ] || [ -e AGENTS.override.md ]; } && signals="$signals codex"
{ [ -e AGENTS.md ] || [ -d .agents ]; } && signals="$signals agents"
{ [ -e GEMINI.md ] || [ -d .gemini ]; } && signals="$signals gemini"
{ [ -d .cursor ] || [ -e .cursorrules ]; } && signals="$signals cursor"
[ -e .github/copilot-instructions.md ] && signals="$signals copilot"
echo "signals:${signals:- none}"

# --- root layout ---
layout=none
if [ -L CLAUDE.md ] && same_file CLAUDE.md AGENTS.md; then
    layout=symlink
elif [ -L AGENTS.md ] && same_file AGENTS.md CLAUDE.md; then
    layout=symlink-reverse
elif [ -f CLAUDE.md ] && [ -f AGENTS.md ]; then
    if grep -qxE '[[:space:]]*@\.?/?AGENTS\.md[[:space:]]*' CLAUDE.md; then
        layout=import
    elif cmp -s CLAUDE.md AGENTS.md; then
        layout=pair-identical
    else
        layout=pair-drifted
    fi
elif [ -f CLAUDE.md ]; then
    layout=claude-only
elif [ -f AGENTS.md ]; then
    layout=agents-only
fi
echo "layout: $layout"

# --- root files ---
for f in AGENTS.md AGENTS.override.md CLAUDE.md .claude/CLAUDE.md CLAUDE.local.md GEMINI.md .github/copilot-instructions.md; do
    if [ -L "$f" ]; then
        echo "file: $f link=$(readlink "$f")"
    elif [ -f "$f" ]; then
        echo "file: $f lines=$(count_lines "$f") bytes=$(count_bytes "$f")"
        warn_if_long "$f"
    fi
done

# --- @imports (Claude Code only), one level, only targets that exist ---
count_imports_of() {
    local src="$1" dir token target
    dir="$(dirname "$src")"
    for token in $(grep -oE '(^|[[:space:]])@[A-Za-z0-9_./~-]+' "$src" 2>/dev/null | tr -d ' \t'); do
        target="${token#@}"
        case "$target" in
            "~/"*) target="$HOME/${target#\~/}" ;;
            /*) ;;
            *) target="$dir/$target" ;;
        esac
        [ -f "$target" ] || continue
        echo "import: $src $token"
        add_claude "$target"
    done
}

# --- Claude Code startup set ---
claude_main=""
if [ -e CLAUDE.md ]; then
    claude_main=CLAUDE.md
elif [ -e AGENTS.md ] && [ ! -e .claude/CLAUDE.md ] && [ ! -e CLAUDE.local.md ]; then
    claude_main=AGENTS.md   # Claude Code's AGENTS.md fallback, default setting
fi
for f in $claude_main .claude/CLAUDE.md CLAUDE.local.md; do
    [ -f "$f" ] || continue
    add_claude "$f"
    count_imports_of "$f"
done

# --- .claude/rules: unscoped load at start, scoped on a matching read ---
# A rule is scoped when its leading frontmatter block has a paths: key.
is_scoped() {
    awk 'NR == 1 { if ($0 != "---") exit 1; next }
         $0 == "---" { exit found ? 0 : 1 }
         /^paths:/ { found = 1 }
         END { exit found ? 0 : 1 }' "$1"
}
if [ -d .claude/rules ]; then
    while IFS= read -r r; do
        if is_scoped "$r"; then
            echo "rule: $r scoped lines=$(count_lines "$r") bytes=$(count_bytes "$r")"
        else
            echo "rule: $r unscoped lines=$(count_lines "$r") bytes=$(count_bytes "$r")"
            add_claude "$r"
        fi
    done < <(find -L .claude/rules -name '*.md' -type f | sort)
fi

# --- Codex startup set (root only: Codex reads root -> working directory) ---
if [ -f AGENTS.override.md ]; then
    add_codex AGENTS.override.md
elif [ -f AGENTS.md ]; then
    add_codex AGENTS.md
fi

# --- nested instruction files: load on demand (Claude Code) or only below the launch folder (Codex) ---
prune_expr=""
for d in $PRUNE_DIRS; do prune_expr="$prune_expr -name $d -o"; done
prune_expr="$prune_expr -path ./.claude/worktrees -o -path ./.worktrees"

# True when a path sits inside another checkout (a worktree or nested repository has its own .git).
in_other_checkout() {
    local d
    d="$(dirname "$1")"
    while [ "$d" != "." ] && [ "$d" != "/" ]; do
        [ -e "$d/.git" ] && return 0
        d="$(dirname "$d")"
    done
    return 1
}
# shellcheck disable=SC2086
find . \( -type d \( $prune_expr \) -prune \) -o \
    \( \( -name CLAUDE.md -o -name AGENTS.md -o -name AGENTS.override.md -o -name CLAUDE.local.md \) -print \) \
    | sed 's|^\./||' | grep '/' | grep -v '^\.claude/CLAUDE\.md$' | sort | while IFS= read -r n; do
    in_other_checkout "$n" && continue
    if [ -L "$n" ]; then
        echo "nested: $n link=$(readlink "$n")"
    else
        echo "nested: $n lines=$(count_lines "$n") bytes=$(count_bytes "$n")"
        warn_if_long "$n"
    fi
done

# --- skills ---
for d in .claude/skills .agents/skills; do
    [ -d "$d" ] || continue
    for s in "$d"/*/SKILL.md; do [ -f "$s" ] && echo "skill: $s"; done
done
if [ -d skills ]; then
    for s in skills/*/SKILL.md; do [ -f "$s" ] && echo "skill-candidate: $s"; done
fi

# --- totals ---
echo "startup: claude lines=$claude_lines bytes=$claude_bytes"
echo "startup: codex lines=$codex_lines bytes=$codex_bytes"
if [ "$codex_bytes" -gt "$CODEX_MAX_BYTES" ]; then
    echo "warn: codex startup is $codex_bytes bytes, over the $CODEX_MAX_BYTES-byte limit; Codex truncates the rest"
fi
exit 0
