---
name: voice-maintain
description: Use when the author asks to review, maintain, clean up or consolidate their personal voice profile, to promote pending voice observations into rules or change a voice rule, when they accept a suggestion to run voice maintenance, or when they want to switch a project's voice store between personal and versioned (for example "share the project glossary with the team").
allowed-tools: Bash(git rev-parse:*)
---

# Maintain the voice profile

Turn pending observations into rules and keep the stores small, consistent and
current — changing only what the author approves, item by item.

## Hard rules

1. **Start only on request.** Run when the author asks, or accepts a
   suggestion to run maintenance. Never start on your own.
2. **Recap, then stop.** Present the numbered recap and end your turn. Change
   no file until the author names the items to apply, or replies "all", which
   applies every item that needs no decision (`references/recap.md` §Reading
   the reply). The one write that needs no item is the run date at the end of
   the run.
3. **Vague replies are not authorization.** "ok", "yes", "go ahead", "sounds
   good" → ask for the item numbers, and change nothing.
4. **Personal never goes to a project store**, whatever the author approves.
5. **Re-read before writing.** If a target file changed since the recap, stop
   that item and show it again.

## Stores

- **Global store**: `${user_config.store_dir}`
- **Project store**: `.personal-voice/` at the project root, if it exists. The
  project root is the directory `git rev-parse --show-toplevel` prints, or the
  working directory outside git; a session started in a subdirectory uses the
  same root.
- **Format and routing**: `${CLAUDE_PLUGIN_ROOT}/shared/store-format.md`. Read
  it first.

If the global store path above is empty or still contains the text
`user_config.store_dir`, tell the author to set **Voice store directory** in
`/config` and stop.

Use the Glob, Read, Write and Edit tools on store files, not shell commands.
The one command this skill runs without asking is `git rev-parse` (the project
root, and the exclude file for a git-choice switch), which it pre-approves.
`git rm -r --cached .personal-voice` runs only when the author asks for it
during a git-choice switch, with a permission prompt.

## Workflow

1. **Read** every file of both stores. Note today's date.
2. **Build proposals** with the checks in `references/checks.md`: promotions,
   reinforcements, merges, conflicts, rules that add nothing, stale rules,
   expired observations, size limits, exemplar limits, scope moves.
3. **Recap** exactly as `references/recap.md` describes, then end your turn.
4. **Parse the reply** into explicit item decisions (`references/recap.md`
   §Reading the reply). Echo what will be applied.
5. **Apply** only those items (`references/apply.md`), then record the run
   date and give the final report.

A request to switch the project store between personal and versioned follows
`references/git-choice.md`, inside or outside a maintenance run.

## Red flags

| Thought | Reality |
|---|---|
| "They said ok, so apply everything" | Not item numbers. Ask. |
| "This observation is obviously right; I'll promote it while listing" | Recap first. Every change is an item. |
| "The stale rule is clearly dead" | Flag it. Keep it unless the author approves removal. |
| "They kept it last time, so I'll flag it again" | A kept rule carries `reviewed:`; it is stale again only six months after that date. |
| "All its evidence is from another project, so move it there" | Only the current project's store is reachable. Add a note instead. |
| "The tag says `backend`, like this repo, so it's ours" | Compare the whole project-root path; folder names repeat across repositories. |
| "The limit is only 51, close enough" | Propose a merge or removal in the same recap. |
| "The family nickname is used everywhere, move it to the project" | Personal material never enters a project store. |
