# Proposals

## Item format

Project proposals (group A), at most 5, ranked by impact:

```
A1. <path> (project)
    incident: <what happened in this session>
    a) <change>  (net ±N lines)  [⚠ growth]
       before: <exact text, or "—" for an insertion>
       after:  <exact text, or "—" for a deletion>
    b) …
    review: OK | REVISED (<what changed>) | DROPPED (<reason>) | —
```

- 1 to 3 options; option a is the smallest change that fixes the incident.
- Prefer deleting, merging or tightening text over adding it. `⚠ growth` marks an option that adds net
  lines of instruction text.
- A JSON target must stay valid JSON.
- Memory promotion: the target is a project file, the incident names the memory file; memory stays as is.

External advice (group B) and pointers (group C):

```
B1. <asset> (<origin>) — owner: <route>
    incident: <what happened>   suggestion: <the change, in one or two lines>
C1. <finding> → <feature or skill>
```

## Review

When a proposal edits a skill, agent, rule, CLAUDE.md, command or output style, dispatch one reviewer for
all such proposals. Use the agent whose type ends in `kaizen-reviewer`. If it is not available, use a
general-purpose subagent. Pass the instructions, checklist and output format below, every proposal with
its options, the target paths, and the paths of the instruction files loaded in the session.

Instructions: never edit anything. Read every listed instruction file, then each target in full. Judge
only the proposed after-text, never text that already exists. Cite `file:line` for every finding. When
unsure between REVISE and DROP, choose the one that leaves less text. Checklist:

1. CONTRADICTS: conflicts with a listed instruction file or with the rest of its target.
2. DUPLICATES: the rule already exists elsewhere; point to it or drop the option.
3. LONGER-THAN-NEEDED: give the shortest text that fixes the incident.
4. OFF-INCIDENT: does more than fix the cited incident, or is general advice.
5. TRIGGER/FRONTMATTER: a description change widens triggers or overlaps a sibling skill; keys invalid
   for the asset type; agent tools broader than needed.
6. GROWTH: adds net text without saying why deleting or merging would not work.

Output, one line per option, then a summary:

```
#A1a OK
#A1b REVISE CONTRADICTS .claude/rules/style.md:4
     after: <minimal replacement>
#A2a DROP OFF-INCIDENT — <reason>
Summary: <k> OK · <m> REVISE · <n> DROP
```

REVISE replaces the option's after-text and the item shows `REVISED`. DROP removes the option; an item
with no option left moves to "Dropped by review" with the reason.

## Recap

```
kaizen — <i> incidents · <a> proposals · <b> advice · <c> pointers
A. Project proposals      (items as above)
B. External advice
C. Pointers
Dropped by review          (one line each)
```

Closing line, then end the turn:
"Nothing has been changed. Reply with item IDs and the option letter where shown (e.g. `apply A1b, A3`).
B and C items are advice and are never applied."

## Authorization

- Only A items named in the user's reply in this run authorize an apply. Echo the authorized set first.
- Not authorization: "ok", "sounds good", "go ahead", "yes", emoji, silence. Re-prompt with the valid IDs.
- An item with options named without a letter: ask which option.
- A B or C item named: reply that it is advice and nothing will be applied.
- Named IDs plus vague approval of others ("A1a, the rest looks fine"): echo the named IDs, ask about the
  rest, apply nothing until the user answers.
- A change the user dictates to an option: echo the new after-text, then apply it as authorized.

## Apply

- Before the first edit, re-read every authorized target once. A target that changed since the recap,
  moved, was deleted, or has uncommitted changes (`git status --porcelain -- FILE`) is not edited: say
  what you found and ask. Your own edits during this apply do not count as changes.
- Edit only the authorized text and leave every other byte as it was. Re-parse an edited JSON file; if
  it is invalid, put the before-text back and report it.

## Final report

Applied IDs; IDs not applied, with the reason; how to undo (`git diff -- FILE`, `git checkout -- FILE`);
the pointers again; for an edited instruction file, `/doctor prompt-audit FILE` if it is available.
