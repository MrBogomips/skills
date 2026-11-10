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

write_manifest() {
    local dir="$1" plugins="$2"
    cat > "$dir/.claude-plugin/marketplace.json" <<EOF
{
  "name": "test-skills",
  "owner": { "name": "Tester" },
  "plugins": [$plugins]
}
EOF
}

entry() {
    local name="$1" version="${2:-0.1.0}" source="${3:-./}" strict="${4:-false}" path="${5:-./skills/$1}"
    printf '{"name":"%s","source":"%s","strict":%s,"description":"d","version":"%s","skills":["%s"]}' \
        "$name" "$source" "$strict" "$version" "$path"
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

d="$(new_repo empty)"; write_manifest "$d" ""
expect_pass "empty marketplace, no skills" "$d"

d="$(new_repo valid)"; write_skill "$d" alpha; write_skill "$d" beta-two
write_manifest "$d" "$(entry alpha),$(entry beta-two 1.2.3)"
expect_pass "two valid skills" "$d"

d="$(new_repo folded)"; mkdir -p "$d/skills/folded"
printf -- '---\nname: folded\ndescription: >\n  Spans two lines.\n  Use when testing.\n---\n' > "$d/skills/folded/SKILL.md"
write_manifest "$d" "$(entry folded)"
expect_pass "folded multi-line description" "$d"

d="$(new_repo missing)"; write_manifest "$d" "$(entry ghost)"
expect_fail "manifest path without SKILL.md" "$d" "MISSING"

d="$(new_repo mismatch)"; write_skill "$d" alpha renamed; write_manifest "$d" "$(entry alpha)"
expect_fail "frontmatter name differs from directory" "$d" "NAME MISMATCH"

d="$(new_repo unlisted)"; write_skill "$d" alpha; write_skill "$d" stray; write_manifest "$d" "$(entry alpha)"
expect_fail "skill directory missing from manifest" "$d" "UNLISTED.*stray"

d="$(new_repo strict)"; write_skill "$d" alpha; write_manifest "$d" "$(entry alpha 0.1.0 ./ true)"
expect_fail "entry with strict true" "$d" "strict must be false"

d="$(new_repo source)"; write_skill "$d" alpha; write_manifest "$d" "$(entry alpha 0.1.0 ./skills/alpha)"
expect_fail "entry with source other than ./" "$d" "source must be"

d="$(new_repo path)"; write_skill "$d" alpha; write_skill "$d" beta
write_manifest "$d" "$(entry alpha 0.1.0 ./ false ./skills/beta),$(entry beta)"
expect_fail "entry whose skill path is not its own" "$d" "alpha: skills must be"

d="$(new_repo version)"; write_skill "$d" alpha; write_manifest "$d" "$(entry alpha v1)"
expect_fail "non-semver version" "$d" "is not semver"

d="$(new_repo dup)"; write_skill "$d" alpha; write_manifest "$d" "$(entry alpha),$(entry alpha)"
expect_fail "duplicate plugin name" "$d" "duplicate plugin name"

d="$(new_repo badname)"; write_skill "$d" Bad_Name; write_manifest "$d" "$(entry Bad_Name)"
expect_fail "name not lowercase-hyphen" "$d" "lowercase letters"

d="$(new_repo longdesc)"; write_skill "$d" alpha alpha "$(printf 'x%.0s' $(seq 1 1025))"
write_manifest "$d" "$(entry alpha)"
expect_fail "description over 1024 characters" "$d" "description is 1025 characters"

d="$(new_repo nodesc)"; mkdir -p "$d/skills/alpha"
printf -- '---\nname: alpha\n---\n' > "$d/skills/alpha/SKILL.md"; write_manifest "$d" "$(entry alpha)"
expect_fail "missing description" "$d" "description missing"

d="$(new_repo badjson)"; printf '{ not json' > "$d/.claude-plugin/marketplace.json"
expect_fail "invalid marketplace.json" "$d" "not valid JSON"

echo ""
if [[ $FAILURES -gt 0 ]]; then
    echo "selftest: $FAILURES case(s) failed"
    exit 1
fi
echo "selftest: all cases passed"
