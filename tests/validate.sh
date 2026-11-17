#!/usr/bin/env bash
# Structural validation: .claude-plugin/plugin.json describes one plugin that ships
# every skill under skills/, and each skill has Agent Skills-compliant frontmatter.
# Catches what `claude plugin validate --strict` does not: a skill directory without
# a SKILL.md, frontmatter names that differ from their directory, a `skills` field
# that would stop Claude Code from loading all of skills/, a stray marketplace.json.
#
# Usage: bash tests/validate.sh [repo-root]    (requires jq; bash 3.2 compatible)
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
MANIFEST="$ROOT/.claude-plugin/plugin.json"
MARKETPLACE="$ROOT/.claude-plugin/marketplace.json"
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

check_plugin() {
    local name version
    name="$(jq -r '.name // empty' "$MANIFEST")"
    version="$(jq -r '.version // empty' "$MANIFEST")"
    PLUGIN="$name@$version"

    if [[ -z "$name" ]]; then
        error "plugin.json: name missing"
    elif ! [[ "$name" =~ $NAME_RE ]]; then
        error "plugin.json: name '$name' must be lowercase letters, digits and single hyphens"
    elif [[ "$name" =~ $RESERVED_PREFIX_RE ]]; then
        error "plugin.json: name '$name' starts with a reserved prefix (claude-, anthropic-, anthropics-, cc-plugin-)"
    fi
    if ! [[ "$version" =~ $SEMVER_RE ]]; then error "plugin.json: version '$version' is not semver"; fi
    if [[ -z "$(jq -r '.description // empty' "$MANIFEST")" ]]; then error "plugin.json: description missing"; fi
    if jq -e 'has("skills")' "$MANIFEST" >/dev/null; then
        error "plugin.json: remove the skills field, so Claude Code loads every skill under skills/"
    fi
}

check_skills() {
    local d
    COUNT=0
    for d in "$ROOT"/skills/*/; do
        [[ -d "$d" ]] || continue
        d="${d%/}"
        check_skill "$d" "./skills/$(basename "$d")"
        COUNT=$((COUNT + 1))
    done
}

command -v jq >/dev/null 2>&1 || fatal "jq is required (brew install jq / apt-get install jq)"
[[ -f "$MANIFEST" ]] || fatal "missing $MANIFEST"
jq empty "$MANIFEST" 2>/dev/null || fatal "plugin.json is not valid JSON"
jq -e 'type == "object"' "$MANIFEST" >/dev/null || fatal "plugin.json must be a JSON object"
if [[ -e "$MARKETPLACE" ]]; then
    error "STRAY marketplace.json: the marketplace lives in its own repository, this one ships only the plugin"
fi

check_plugin
check_skills

if [[ $ERRORS -gt 0 ]]; then
    echo "FAILED: $ERRORS error(s)"
    exit 1
fi
echo "OK: $COUNT skill(s) in plugin $PLUGIN"
