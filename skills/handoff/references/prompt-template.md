# Prompt template

Write the prompt in the language of the conversation with the user, headings included: the English names below
are placeholders to translate. Address the recipient as "you" and make it ready to paste. Use the parts below in
this order. A part with nothing to say is left out together with its heading.

```markdown
# Handoff: <topic>

<date> · <remote URL> · branch <branch> · base <short SHA> · for <recipient kind>

## Goal
## State
## Decisions
## Constraints
## References
## Dead ends
## How to verify
## First step
```

If the recipient is likely to have skills or tools that fit the first step, add a last part, "Suggested skills and
tools", naming them. Otherwise the prompt ends with First step.

| Part | Content |
|---|---|
| Goal | What the work is for and what you ask the recipient to do, in two or three sentences. |
| State | Done, in progress, to do. For each item, where it lives: commit, `changes.patch`, inline diff, file. |
| Decisions | Each decision with its reason and the alternatives rejected. Mark the user's own decisions as settled. |
| Constraints | The user's constraints and preferences that apply to this work. |
| References | Files, branches, commits, issues, pull requests, documents. Cite existing plans, specs and issues by path or URL instead of restating them. |
| Dead ends | What was tried and failed, why, and known traps. |
| How to verify | Exact commands and the expected result. |
| First step | The one concrete action to start with. |

## Topic only

Every line serves the topic. One addition, keyed to what the recipient will see: if the working tree, patch or
zip they receive contains changes outside the topic, add one line under State naming those changes as not part
of this work. Recipients elsewhere get a patch with topic files only, so for them the line is usually absent.

## Paths and shipped material

- Same machine: absolute paths.
- Unknown recipient: the repository root written with `~` for the home directory, then repo-relative paths, with
  remote URL, branch and commit in the header line.
- Anyone else: repo-relative paths, with remote URL, branch and commit in the header line.
- In a zip, cite shipped copies as `assets/...` and the patch as `changes.patch`.
- With a patch or an inline diff, State gives the base SHA and the commands to apply it:

```bash
git fetch <remote>
git switch -c <branch> <base SHA>
git apply changes.patch        # inline diff: save the diff block to changes.patch first
```

`<remote>` is the recipient's name for the remote in the header line, usually `origin`.

## Example

```markdown
# Handoff: fix bug 22, day-first dates in supplier CSVs

2026-11-10 · https://github.com/acme/invoice-parser · branch fix/bug22-date-format · base 6ca41db · for a colleague

## Goal
Supplier CSVs use day-first dates and the parser reads them month-first. Finish the fix and open the PR.

## State
- Done: tests reproducing the bug (6ca41db, on the remote).
- In progress: explicit format list and two-digit years in `invoice_parser/dates.py`, in `changes.patch`.
- To do: a test for `tests/data/two_digit_years.csv` (in the patch); century rule for two-digit years.

Apply the patch on the base:

    git fetch origin
    git switch -c fix/bug22-date-format 6ca41db
    git apply changes.patch

## Decisions
- Explicit list of formats, no new dependency (settled by the user). Rejected: `dateutil` with `dayfirst=True`,
  which misreads ambiguous ISO dates.

## How to verify
`python -m pytest` from the repository root: all tests pass.

## First step
Apply the patch, then write the two-digit-year test.
```
