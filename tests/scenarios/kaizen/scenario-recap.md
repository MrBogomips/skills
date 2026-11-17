# Scenario: Recap after a session with incidents

## Setup
Fresh fixture and turn 1 (see README). Record the `before` fingerprint after turn 1.

## Invocation
Turn 2: `/kaizen`.

## Expected Behavior
1. Links the `make test` failure to K-a, the indentation choice to K-b, the `lib/` rework to K-c and the
   `stylecheck` failure to K-d, each with the asset's path and line.
2. Routes K-a, K-b and K-c to group A, K-d to group B, and K-f to group C or leaves it out.
3. Shows A items with options, before and after text, net lines and a review verdict.
4. Ends with the "Nothing has been changed…" line and stops.

## Acceptance Criteria
- [ ] A contains K-a, K-b and K-c; the K-a item has an option that only replaces the test command (net 0 lines)
- [ ] K-d is a B item naming `fixture-tools` as a plugin and `https://example.invalid/fixture-tools` as the owner; no edit is proposed for it
- [ ] K-f is not an A item; if present, it is a C pointer to `/doctor prompt-audit`
- [ ] The recap does not print an inventory of every loaded asset
- [ ] No A item creates a new skill or agent file
- [ ] The fingerprint diff is empty after the turn, and no report or state file exists anywhere under `$F`

## Variant: not a git repository
Setup: `rm -rf "$F/repo/.git"` before turn 1.
- [ ] Every finding is a B item or a C pointer; the recap says nothing is editable outside git
- [ ] The fingerprint diff is empty after the turn

## Variant: memory promotion (K-e)
Setup: before turn 1, write `$F/repo/.claude/settings.local.json` with
`{"autoMemoryDirectory": "<absolute $F>/memory"}`.
- [ ] If the session ran `make check` without failing, the recap proposes adding the fact to CLAUDE.md and names `memory/project_tests.md` as its source
- [ ] No item edits `memory/`; after any apply, `memory/` is unchanged in the fingerprint diff

## Variant: missing reference
Setup: rename `kaizen/skills/kaizen/references/proposals.md` in a scratch copy of the plugin and load that copy.
- [ ] The skill stops and names the missing file; no recap is shown
