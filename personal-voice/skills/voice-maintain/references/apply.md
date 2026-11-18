# Applying

Edit the store with the file tools, one item at a time, so each change can be
reviewed; do not batch items into a shell script.

For each authorized item, in number order:

1. Re-read the target files. If one changed since the recap, stop this item,
   show its new before and after, and ask again.
2. Write the change in the format of the store format's Rule entries:
   - **PROMOTE**: add the rule under its heading, with its qualifiers, evidence
     and `reinforced` date; remove the observation from `observations.md`.
     Create the file with its frontmatter if it is the first rule there.
   - **REINFORCE**: update the rule's evidence and `reinforced` date; remove
     the observation.
   - **MERGE**: replace the rules with the merged one.
   - **CONFLICT**: apply the author's choice.
     - **Rule A against observation B, "keep A"**: leave A as it is and remove
       the observation.
     - **Rule A against observation B, "keep B"**: replace A, at its place in
       the file, with B promoted as a rule (B's evidence, and its latest source
       date as `reinforced`); remove the observation. A's evidence does not
       carry over: it supported the opposite habit.
     - **Rule against rule**: remove the losing rule; the winning rule stays
       unchanged.
     - **Qualify**: the side the author names gets the new qualifier. The other
       side stays as a rule, or is promoted when it is an observation, so each
       applies in its own scope; the observation is removed.
   - **REVIEW** (stale): "keep" adds `reviewed: <today>` to the rule, or updates
     it, and changes nothing else; "remove" removes the rule.
   - **REMOVE**, **DELETE**, **TRIM**: remove or shorten exactly the named
     entry or exemplar.
   - **MOVE**: add the rule to the destination with the evidence summed, then
     remove it from the source. Refuse a move of personal material into a
     project store, even if approved. The only project store a move can reach
     is the current project's `.personal-voice/`. A move into a project store
     drops the `project:` tags from the sources it carries: the store
     identifies the project, and no absolute path is written into it.
   - Any item whose destination is a project store that does not exist yet
     (a MOVE, or a promotion with "scope: project"): first run the store
     format's Project store initialization. If the author chooses Skip, skip
     the item and say so.
   - Edited text or a changed scope from the reply replaces the proposal's.
3. Keep every rule file at 50 rules or fewer. If an applied promotion would
   break the limit because its linked merge or removal was not approved, skip
   the promotion and say so.

Then:

- Set `last_maintenance` to today in the global `observations.md`, creating
  the file with its frontmatter if needed.
- Final report, in the language of the conversation: applied items, skipped
  items and why, and the pending observations left.
