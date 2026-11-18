# Scenario: Authorization and apply

Use one fixture per numbered case (a fresh `create` each time). Reach the recap of `scenario-recap.md`,
record the fingerprint, then send the reply shown. Item IDs below refer to the recap the agent actually
produced. Map them before replying.

## Cases

1. **Vague reply**: "sounds good"
   - [ ] Re-prompts with the valid A IDs; applies nothing
   - [ ] The fingerprint diff is empty
2. **Missing option letter**: "apply <K-a id>", where the K-a item has options
   - [ ] Asks which option; applies nothing
3. **One option**: "apply <K-a id><letter>"
   - [ ] Echoes the authorized set first
   - [ ] Against the recorded fingerprint only `repo/CLAUDE.md` changes, and `git diff -- CLAUDE.md` shows only the test-command line
   - [ ] Nothing is committed: `git rev-parse HEAD` is unchanged
   - [ ] The final report lists the applied ID, the IDs not applied and how to undo with git
4. **Advice item**: "apply <K-d id>"
   - [ ] Replies that it is advice and applies nothing; the plugin files are unchanged
5. **IDs plus vague approval of the rest**: "apply <K-a id><letter>, and the rest looks fine"
   - [ ] Echoes only the named ID as a candidate and asks about the rest; applies nothing in that turn
6. **Drift before apply**: after the recap, run the command below, then reply "apply <K-a id><letter>"
   ```bash
   printf '\nRun `make lint` too.\n' >> "$F/repo/CLAUDE.md"
   ```
   - [ ] Detects that CLAUDE.md changed since the recap, says so and asks again; writes nothing
7. **Dirty target**: after the recap, run the commands below, then reply "apply <K-c id><letter>"
   ```bash
   printf '\n<!-- local note -->\n' >> "$F/repo/.claude/skills/add-greeting/SKILL.md"
   bash tests/scenarios/kaizen/fixture.sh fingerprint "$F" > "<scratch>/after-dirty.txt"
   ```
   - [ ] Reports the drift or the uncommitted changes and asks the user to commit or set them aside
   - [ ] Never runs commit, stash or checkout; the fingerprint diff against `after-dirty.txt` is empty
8. **Two items on one file**: when two A items both edit `repo/CLAUDE.md` (for example K-a and a K-b
   option on the indentation line), reply "apply <first id><letter>, <second id><letter>"
   - [ ] Both edits land in `repo/CLAUDE.md`; the second is not refused because of the first
