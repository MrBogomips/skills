#!/usr/bin/env bash
# Structural validation: .claude-plugin/plugin.json describes the root plugin that ships
# every skill under skills/; each top-level folder with its own .claude-plugin/plugin.json
# is a separate plugin named after its folder; every skill has Agent Skills-compliant
# frontmatter. Catches what `claude plugin validate --strict` does not: a skill directory
# without a SKILL.md, frontmatter names that differ from their directory, a `skills` field
# that would stop Claude Code from loading all of a plugin's skills/, a plugin folder whose
# name differs from its plugin, a stray marketplace.json.
#
# Usage: bash tests/validate.sh [repo-root]    (requires jq; bash 3.2 compatible)
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
MANIFEST="$ROOT/.claude-plugin/plugin.json"
RESERVED_PREFIX_RE='^(claude|anthropic|anthropics|cc-plugin)-'
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

# check_plugin <manifest> <label> [expected-name]: prints name@version on success.
check_plugin() {
    local manifest="$1" label="$2" expected="${3:-}" name version
    if ! jq empty "$manifest" 2>/dev/null; then error "$label: not valid JSON"; return; fi
    if ! jq -e 'type == "object"' "$manifest" >/dev/null; then error "$label: must be a JSON object"; return; fi
    name="$(jq -r '.name // empty' "$manifest")"
    version="$(jq -r '.version // empty' "$manifest")"
    LAST_PLUGIN="$name@$version"

    if [[ -z "$name" ]]; then
        error "$label: name missing"
    elif ! [[ "$name" =~ $NAME_RE ]]; then
        error "$label: name '$name' must be lowercase letters, digits and single hyphens"
    elif [[ "$name" =~ $RESERVED_PREFIX_RE ]]; then
        error "$label: name '$name' starts with a reserved prefix (claude-, anthropic-, anthropics-, cc-plugin-)"
    elif [[ -n "$expected" && "$name" != "$expected" ]]; then
        error "PLUGIN NAME MISMATCH $label: name '$name' differs from folder '$expected'"
    fi
    if ! [[ "$version" =~ $SEMVER_RE ]]; then error "$label: version '$version' is not semver"; fi
    if [[ -z "$(jq -r '.description // empty' "$manifest")" ]]; then error "$label: description missing"; fi
    if jq -e 'has("skills")' "$manifest" >/dev/null; then
        error "$label: remove the skills field, so Claude Code loads every skill under skills/"
    fi
    if [[ -e "$(dirname "$manifest")/marketplace.json" ]]; then
        error "STRAY marketplace.json next to $label: the marketplace lives in its own repository"
    fi
}

# check_skills <plugin-dir> <rel-prefix>: sets COUNT to the number of skill folders.
check_skills() {
    local base="$1" prefix="$2" d
    COUNT=0
    for d in "$base"/skills/*/; do
        [[ -d "$d" ]] || continue
        d="${d%/}"
        check_skill "$d" "$prefix/skills/$(basename "$d")"
        COUNT=$((COUNT + 1))
    done
}

command -v jq >/dev/null 2>&1 || fatal "jq is required (brew install jq / apt-get install jq)"
[[ -f "$MANIFEST" ]] || fatal "missing $MANIFEST"
jq empty "$MANIFEST" 2>/dev/null || fatal "plugin.json is not valid JSON"

check_plugin "$MANIFEST" "plugin.json"
ROOT_PLUGIN="$LAST_PLUGIN"
check_skills "$ROOT" "."
SUMMARY="OK: $COUNT skill(s) in plugin $ROOT_PLUGIN"

# Top-level plugin folders: <folder>/.claude-plugin/plugin.json, named after the folder.
for m in "$ROOT"/*/.claude-plugin/plugin.json; do
    [[ -f "$m" ]] || continue
    dir="$(dirname "$(dirname "$m")")"
    folder="$(basename "$dir")"
    check_plugin "$m" "$folder/.claude-plugin/plugin.json" "$folder"
    check_skills "$dir" "./$folder"
    SUMMARY="$SUMMARY; plugin $LAST_PLUGIN with $COUNT skill(s)"
done

if [[ $ERRORS -gt 0 ]]; then
    echo "FAILED: $ERRORS error(s)"
    exit 1
fi
echo "$SUMMARY"
