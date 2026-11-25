#!/bin/bash
# Open the official-drift issue with the body in $1, or comment on the one already open.
# Usage: bash open_drift_issue.sh <body-file>   (needs gh, authenticated through GH_TOKEN)
set -euo pipefail

body="$1"
label="official-drift"
title="Official skills or docs changed: review skill-maker's rulebook"

gh label create "$label" --color FBCA04 --description "$title" --force
open_issue=$(gh issue list --label "$label" --state open --json number -q '.[0].number')
if [ -n "$open_issue" ]; then
  gh issue comment "$open_issue" --body-file "$body"
else
  gh issue create --title "$title" --label "$label" --body-file "$body"
fi
