#!/usr/bin/env bash
# Structural validation: .claude-plugin/marketplace.json and skills/ must describe
# the same skills, one plugin per skill, with Agent Skills-compliant frontmatter.
# Catches what `claude plugin validate --strict` does not: manifest paths without a
# SKILL.md, frontmatter names that differ from their directory, unlisted skills.
#
# Usage: bash tests/validate.sh [repo-root]    (requires jq; bash 3.2 compatible)
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
MANIFEST="$ROOT/.claude-plugin/marketplace.json"
NAME_RE='^[a-z0-9]+(-[a-z0-9]+)*$'
SEMVER_RE='^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$'
MAX_NAME=64
MAX_DESCRIPTION=1024
ERRORS=0

error() { echo "ERROR: $*"; ERRORS=$((ERRORS + 1)); }
fatal() { echo "ERROR: $*"; exit 1; }

# Prints a top-level scalar from SKILL.md frontmatter; folded/literal blocks are joined.
frontmatter_value() {
    local key="$1" file="$2"
    awk -v key="$key" -v q="'" '
        NR == 1 { if ($0 != "---") exit; next }
        /^---[ \t]*$/ { exit }
        block && /^[ \t]/ { line = $0; sub(/^[ \t]+/, "", line); out = out (out == "" ? "" : " ") line; next }
        block { exit }
        index($0, key ":") == 1 {
            v = substr($0, length(key) + 2); sub(/^[ \t]+/, "", v); sub(/[ \t]+$/, "", v)
            if (v ~ /^[>|][-+]?$/) { block = 1; next }
            gsub("^[\"" q "]|[\"" q "]$", "", v); print v; exit
        }
        END { if (block) print out }
    ' "$file"
}

check_skill() {
    local dir="$1" rel="$2" file="$1/SKILL.md" name description
    if [[ ! -f "$file" ]]; then error "MISSING $rel/SKILL.md"; return; fi
    if [[ "$(head -1 "$file")" != "---" ]]; then error "$rel/SKILL.md: no YAML frontmatter"; return; fi

    name="$(frontmatter_value name "$file")"
    description="$(frontmatter_value description "$file")"

    if [[ -z "$name" ]]; then
        error "$rel/SKILL.md: frontmatter name missing"
    elif [[ "$name" != "$(basename "$dir")" ]]; then
        error "NAME MISMATCH $rel/SKILL.md: name '$name' differs from directory '$(basename "$dir")'"
    fi
    if [[ -n "$name" ]] && { ! [[ "$name" =~ $NAME_RE ]] || [[ ${#name} -gt $MAX_NAME ]]; }; then
        error "$rel/SKILL.md: name '$name' must be lowercase letters, digits and single hyphens, max $MAX_NAME"
    fi
    if [[ -z "$description" ]]; then
        error "$rel/SKILL.md: frontmatter description missing"
    elif [[ ${#description} -gt $MAX_DESCRIPTION ]]; then
        error "$rel/SKILL.md: description is ${#description} characters (max $MAX_DESCRIPTION)"
    fi
}

field() { jq -r ".plugins[$1].$2 // empty" "$MANIFEST"; }

check_entry() {
    local i="$1" name source strict version skills
    name="$(field "$i" name)"
    source="$(field "$i" source)"
    strict="$(jq -r ".plugins[$i].strict" "$MANIFEST")"
    version="$(field "$i" version)"
    skills="$(jq -c ".plugins[$i].skills // []" "$MANIFEST")"

    if [[ -z "$name" ]]; then error "plugins[$i]: name missing"; return; fi
    if ! [[ "$name" =~ $NAME_RE ]]; then error "$name: plugin name must be lowercase letters, digits and single hyphens"; fi
    if printf '%s\n' "$SEEN" | grep -qxF "$name"; then error "$name: duplicate plugin name"; fi
    SEEN="$(printf '%s\n%s' "$SEEN" "$name")"

    if [[ "$source" != "./" ]]; then error "$name: source must be \"./\" (found \"$source\")"; fi
    if [[ "$strict" != "false" ]]; then error "$name: strict must be false (found $strict)"; fi
    if [[ -z "$(field "$i" description)" ]]; then error "$name: description missing"; fi
    if ! [[ "$version" =~ $SEMVER_RE ]]; then error "$name: version '$version' is not semver"; fi
    if [[ "$skills" != "[\"./skills/$name\"]" ]]; then
        error "$name: skills must be [\"./skills/$name\"] (found $skills)"
    fi

    local path
    for path in $(jq -r ".plugins[$i].skills[]?" "$MANIFEST"); do
        check_skill "$ROOT/${path#./}" "$path"
    done
}

check_unlisted() {
    local d rel
    for d in "$ROOT"/skills/*/; do
        [[ -d "$d" ]] || continue
        rel="./skills/$(basename "$d")"
        jq -e --arg p "$rel" '[.plugins[].skills[]?] | index($p) != null' "$MANIFEST" >/dev/null \
            || error "UNLISTED $rel: not declared in marketplace.json"
    done
}

command -v jq >/dev/null 2>&1 || fatal "jq is required (brew install jq / apt-get install jq)"
[[ -f "$MANIFEST" ]] || fatal "missing $MANIFEST"
jq empty "$MANIFEST" 2>/dev/null || fatal "marketplace.json is not valid JSON"
jq -e '.plugins | type == "array"' "$MANIFEST" >/dev/null || fatal "marketplace.json: plugins must be an array"
[[ -n "$(jq -r '.name // empty' "$MANIFEST")" ]] || error "marketplace.json: name missing"
[[ -n "$(jq -r '.owner.name // empty' "$MANIFEST")" ]] || error "marketplace.json: owner.name missing"

SEEN=""
COUNT="$(jq '.plugins | length' "$MANIFEST")"
i=0
while [[ $i -lt $COUNT ]]; do
    check_entry "$i"
    i=$((i + 1))
done
check_unlisted

if [[ $ERRORS -gt 0 ]]; then
    echo "FAILED: $ERRORS error(s)"
    exit 1
fi
echo "OK: $COUNT skill(s); marketplace.json and skills/ agree"
