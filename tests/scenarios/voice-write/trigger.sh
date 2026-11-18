#!/usr/bin/env bash
# Layer 2 helper: runs one headless Claude Code session with the personal-voice
# plugin loaded from this repository and prints the skills the model invoked.
# Checks description triggering only; the store does not need to be configured.
# With --marketplace (or PV_TRIGGER_MARKETPLACE=1) it loads every plugin of the
# repository instead, so collisions with other skills are measured too.
# usage: bash trigger.sh [--marketplace] WORKDIR "prompt"
set -euo pipefail

usage() { echo "usage: $0 [--marketplace] WORKDIR PROMPT" >&2; exit 2; }

marketplace="${PV_TRIGGER_MARKETPLACE:-0}"
if [[ "${1:-}" == "--marketplace" ]]; then
    marketplace=1
    shift
fi
[[ $# -eq 2 ]] || usage
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
workdir="$1"
prompt="$2"

plugin_args=()
if [[ "$marketplace" == "1" ]]; then
    for dir in "$REPO_ROOT"/*/; do
        [[ -f "$dir.claude-plugin/plugin.json" ]] && plugin_args+=(--plugin-dir "${dir%/}")
    done
else
    plugin_args=(--plugin-dir "$REPO_ROOT/personal-voice")
fi

mkdir -p "$workdir"
cd "$workdir"

claude -p "$prompt" "${plugin_args[@]}" --permission-mode default \
    --output-format stream-json --verbose 2>/dev/null \
    | jq -r 'select(.type=="assistant") | .message.content[]?
             | select(.type=="tool_use" and .name=="Skill") | .input.skill'
