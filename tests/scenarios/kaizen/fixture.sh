#!/usr/bin/env bash
# Layer 2 fixture for kaizen: builds a disposable project whose assets cause known
# incidents during a scripted task, a local plugin with a faulty skill, and a memory
# dir; or fingerprints their state to prove which files a run wrote.
# macOS/BSD compatible (bash 3.2).
set -euo pipefail

GIT_ID=(-c user.name=fixture -c user.email=fixture@example.invalid)

usage() {
    echo "usage: $0 create DIR | fingerprint DIR" >&2
    exit 2
}

write_repo() {
    local repo="$1"
    mkdir -p "$repo/src" "$repo/tests" "$repo/.claude/rules" "$repo/.claude/skills/add-greeting"

    # K-a: CLAUDE.md says `make test`; the Makefile only has `check`.
    # K-b: the indentation line contradicts .claude/rules/style.md.
    cat > "$repo/CLAUDE.md" <<'EOF'
# CLAUDE.md

## Layout

Shell functions live in `src/`. `src/main.sh` sources every other file in `src/`.

## Tests

Run `make test` before you finish.

## Style

Indent shell code with 2 spaces.
EOF
    printf 'check:\n\t@sh tests/run.sh\n' > "$repo/Makefile"
    cat > "$repo/tests/run.sh" <<'EOF'
#!/bin/sh
. ./src/main.sh
hello >/dev/null && echo "tests passed"
EOF
    cat > "$repo/src/main.sh" <<'EOF'
#!/bin/sh
for f in src/*.sh; do
  [ "$f" = src/main.sh ] || . "./$f"
done
EOF
    printf 'hello() {\n  echo "hello"\n}\n' > "$repo/src/hello.sh"

    printf '# Style\n\nIndent shell code with tabs.\n' > "$repo/.claude/rules/style.md"
    # K-f: two rules that contradict each other; the scripted task never writes docs.
    printf '# Docs\n\nWrite documentation in British English.\n' > "$repo/.claude/rules/docs-uk.md"
    printf '# Docs\n\nWrite documentation in American English.\n' > "$repo/.claude/rules/docs-us.md"

    # K-c: the skill points at lib/, which does not exist, and at a sourcing step main.sh already does.
    cat > "$repo/.claude/skills/add-greeting/SKILL.md" <<'EOF'
---
name: add-greeting
description: "Add a greeting function to this project. Use when asked to add a greet or greeting function."
---

1. Create the function in `lib/greetings.sh`.
2. Add a line to `src/main.sh` that sources `lib/greetings.sh`.
EOF
}

write_plugin() {
    local plugin="$1"
    mkdir -p "$plugin/.claude-plugin" "$plugin/skills/check-style"
    printf '{"name":"fixture-tools","version":"0.1.0","description":"Fixture plugin for kaizen scenarios","repository":"https://example.invalid/fixture-tools"}\n' \
        > "$plugin/.claude-plugin/plugin.json"
    # K-d: the command the skill prescribes does not exist.
    cat > "$plugin/skills/check-style/SKILL.md" <<'EOF'
---
name: check-style
description: "Check the style of shell code. Use when asked to check style."
---

Run `stylecheck --all` from the project root and report its output.
EOF
}

write_memory() {
    local mem="$1"
    mkdir -p "$mem"
    printf '# Memory Index\n\n- [project_tests.md](project_tests.md) — how to run the tests\n' > "$mem/MEMORY.md"
    # K-e: a fact that prevents the K-a error when memory is loaded.
    printf -- '---\nname: project-tests\ndescription: how to run the tests\nmetadata:\n  type: project\n---\n\nTests run with `make check`; there is no `make test` target.\n' \
        > "$mem/project_tests.md"
}

create() {
    local root="$1"
    if [ -e "$root" ]; then
        echo "refusing: $root already exists" >&2
        exit 1
    fi
    write_repo "$root/repo"
    git -C "$root/repo" init -q -b main
    git -C "$root/repo" add -A
    git -C "$root/repo" "${GIT_ID[@]}" commit -qm "init"
    write_plugin "$root/fixture-tools"
    write_memory "$root/memory"
    echo "repo:    $root/repo"
    echo "plugin:  $root/fixture-tools"
    echo "memory:  $root/memory"
}

fingerprint() {
    local root="$1"
    [ -d "$root/repo/.git" ] || { echo "not a fixture: $root" >&2; exit 1; }
    ( cd "$root" && find . -path ./repo/.git -prune -o -type f -print \
        | LC_ALL=C sort | while IFS= read -r f; do cksum "$f"; done )
    git -C "$root/repo" rev-parse HEAD
    git -C "$root/repo" status --porcelain
}

[ "$#" -eq 2 ] || usage
case "$1" in
    create) create "$2" ;;
    fingerprint) fingerprint "$2" ;;
    *) usage ;;
esac
