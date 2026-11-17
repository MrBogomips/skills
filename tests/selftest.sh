#!/usr/bin/env bash
# Self-test for tests/validate.sh: builds throwaway repositories and checks
# that the validator accepts the good ones and rejects each kind of drift.
set -euo pipefail

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
VALIDATE="$TESTS_DIR/validate.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
FAILURES=0

# --- fixture builders -------------------------------------------------------

new_repo() {
    local dir="$WORK/$1"
    mkdir -p "$dir/.claude-plugin"
    printf '%s\n' "$dir"
}

write_plugin() {
    local dir="$1" name="${2:-test-skills}" version="${3:-0.1.0}" extra="${4:-}"
    printf '{"name":"%s","version":"%s","description":"d"%s}\n' "$name" "$version" "$extra" \
        > "$dir/.claude-plugin/plugin.json"
}

write_skill() {
    local dir="$1" folder="$2" name="${3:-$2}" description="${4:-Does a thing. Use when testing.}"
    mkdir -p "$dir/skills/$folder"
    printf -- '---\nname: %s\ndescription: %s\n---\n\n# %s\n' "$name" "$description" "$name" \
        > "$dir/skills/$folder/SKILL.md"
}

# --- assertions -------------------------------------------------------------

expect_pass() {
    local label="$1" dir="$2" out
    if out="$(bash "$VALIDATE" "$dir" 2>&1)"; then
        echo "PASS: $label"
    else
        echo "FAIL: $label (expected success)"; echo "$out" | sed 's/^/    /'
        FAILURES=$((FAILURES + 1))
    fi
}

expect_fail() {
    local label="$1" dir="$2" pattern="$3" out
    if out="$(bash "$VALIDATE" "$dir" 2>&1)"; then
        echo "FAIL: $label (expected failure)"
        FAILURES=$((FAILURES + 1))
    elif ! printf '%s\n' "$out" | grep -qE "$pattern"; then
        echo "FAIL: $label (no line matching /$pattern/)"; echo "$out" | sed 's/^/    /'
        FAILURES=$((FAILURES + 1))
    else
        echo "PASS: $label"
    fi
}

# --- cases ------------------------------------------------------------------

d="$(new_repo empty)"; write_plugin "$d"
expect_pass "plugin with no skills" "$d"

d="$(new_repo valid)"; write_skill "$d" alpha; write_skill "$d" beta-two; write_plugin "$d" test-skills 1.2.3
expect_pass "two valid skills" "$d"

d="$(new_repo folded)"; mkdir -p "$d/skills/folded"
printf -- '---\nname: folded\ndescription: >\n  Spans two lines.\n  Use when testing.\n---\n' > "$d/skills/folded/SKILL.md"
write_plugin "$d"
expect_pass "folded multi-line description" "$d"

d="$(new_repo missing)"; mkdir -p "$d/skills/ghost"; write_plugin "$d"
expect_fail "skill directory without SKILL.md" "$d" "MISSING"

d="$(new_repo mismatch)"; write_skill "$d" alpha renamed; write_plugin "$d"
expect_fail "frontmatter name differs from directory" "$d" "NAME MISMATCH"

d="$(new_repo badname)"; write_skill "$d" Bad_Name; write_plugin "$d"
expect_fail "skill name not lowercase-hyphen" "$d" "lowercase letters"

d="$(new_repo longdesc)"; write_skill "$d" alpha alpha "$(printf 'x%.0s' $(seq 1 1025))"; write_plugin "$d"
expect_fail "description over 1024 characters" "$d" "description is 1025 characters"

d="$(new_repo nodesc)"; mkdir -p "$d/skills/alpha"
printf -- '---\nname: alpha\n---\n' > "$d/skills/alpha/SKILL.md"; write_plugin "$d"
expect_fail "missing description" "$d" "description missing"

d="$(new_repo version)"; write_skill "$d" alpha; write_plugin "$d" test-skills v1
expect_fail "non-semver plugin version" "$d" "is not semver"

d="$(new_repo pluginname)"; write_skill "$d" alpha; write_plugin "$d" Test_Skills
expect_fail "plugin name not lowercase-hyphen" "$d" "plugin.json: name 'Test_Skills'"

d="$(new_repo reserved)"; write_skill "$d" alpha; write_plugin "$d" claude-tools
expect_fail "plugin name with a reserved prefix" "$d" "reserved prefix"

d="$(new_repo skillsfield)"; write_skill "$d" alpha; write_plugin "$d" test-skills 0.1.0 ',"skills":["./skills/alpha"]'
expect_fail "plugin.json declares skills" "$d" "remove the skills field"

d="$(new_repo stray)"; write_skill "$d" alpha; write_plugin "$d"
printf '{"name":"m","owner":{"name":"o"},"plugins":[]}\n' > "$d/.claude-plugin/marketplace.json"
expect_fail "marketplace.json next to the plugin" "$d" "STRAY marketplace.json"

d="$(new_repo nomanifest)"; write_skill "$d" alpha
expect_fail "missing plugin.json" "$d" "missing .*plugin.json"

d="$(new_repo badjson)"; printf '{ not json' > "$d/.claude-plugin/plugin.json"
expect_fail "invalid plugin.json" "$d" "not valid JSON"

echo ""
if [[ $FAILURES -gt 0 ]]; then
    echo "selftest: $FAILURES case(s) failed"
    exit 1
fi
echo "selftest: all cases passed"
