# Scenario: Conflict settled with "keep B", and a rule-against-rule conflict

## Setup
Fixture created. For Case B, add a rule that contradicts "Short sentences, one idea each." before
taking the `before` fingerprint:

```bash
awk '{print} /^- Short sentences, one idea each\./{print "- Long, flowing sentences that join several ideas. (evidence: 2, reinforced: 2026-08-20)"}' \
    "$F/store/core.md" > "$F/core.tmp" && mv "$F/core.tmp" "$F/store/core.md"
```

## Invocation
Run the recap. Note the item number N of the M-conflict item ("Lei" rule A against "tu"
observation B) and, in Case B, the number K of the conflict between the two `core.md` Tone rules.

### Case A — rule against observation
"N keep B"

### Case B — rule against rule
"K keep A" (keep "Short sentences, one idea each.")

## Expected Behavior
- Case A: rule A is replaced, at its place in `languages/it.md › Audiences`, by B promoted as a rule;
  the observation is removed
- Case B: the losing rule is removed and the winning rule is left unchanged

## Acceptance Criteria
Case A:
- [ ] `languages/it.md › Audiences` no longer contains the "Lei" rule
- [ ] In its place: an `[it] [to clients]` rule about "tu" with `evidence: 2` and `reinforced: 2026-09-22` (A's evidence is not added)
- [ ] The "Use 'tu' with clients" observation is gone from `observations.md`; the other observations are unchanged
- [ ] The `[to colleagues]` rule in the same section is unchanged

Case B:
- [ ] The recap shows both `core.md` Tone rules side by side as one CONFLICT item, with their evidence
- [ ] After "K keep A": "Long, flowing sentences…" is gone; "Short sentences, one idea each. (evidence: 4, reinforced: 2026-09-02)" is byte-for-byte unchanged
- [ ] No other rule file changes

## Edge Cases
- "K keep B" in Case B → "Short sentences, one idea each." is removed and "Long, flowing sentences…" stays unchanged
- "N" alone → a question about which side prevails; nothing changes
