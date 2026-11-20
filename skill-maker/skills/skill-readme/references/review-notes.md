# Review notes format

The review notes are the result of a check, and they accompany every draft. They are for the owner
of the component, not for its users.

```markdown
# README review: <plugin name> <version>

Checked on <date> against <plugin root>. Mode: check | draft.

## Inventory

| Component | Kind | README | Result |
|---|---|---|---|
| personal-voice | plugin | README.md | 9 errors |
| voice-write | skill | skills/voice-write/README.md | missing |

Excluded: <SKILL.md files found but not distributed, each with the reason>.

## Findings

### <path of the README>

| # | Section | Kind | Finding | Evidence |
|---|---|---|---|---|
| 1 | Installation | contradiction | Says Node 18; the script requires 22.20 | `scripts/run.sh:4` |
| 2 | Why | value | Measured render time is only in Performance | `README.md:64` |

## Scenarios

| README | Scenario | Observed or illustrative | Source |
|---|---|---|---|

## Kept and moved content

<Draft mode only: what moved from the existing README and where; what could not be placed.>

## Open questions for the owner

<Missing data and decisions only the owner can make, one line each.>
```

## Finding kinds

| Kind | Meaning |
|---|---|
| `structure` | From the lint script: a missing, misspelled, misplaced or empty block. |
| `contradiction` | The README and a source, or two sources, disagree on a fact. |
| `unverified` | The README states something no source confirms. |
| `missing data` | A section needs information no source gives. |
| `value` | Value found in the sources that the Why does not state. |
| `audience` | Text not addressed to the people who evaluate or use the component. |
| `summary` | `summary:` and the introduction say different things. |

## Rules

- Every finding has a path, a section and evidence (`file:line`, or what was searched and where).
- Copy the script findings as they are, with their line numbers. Do not reword or drop them.
- Custom sections reported as notes by the script go in the inventory result, not in the findings.
- No finding for wording that differs between the README and the manifest or `SKILL.md` descriptions
  when the facts agree.
- Order the findings of a file by section, in contract order.
