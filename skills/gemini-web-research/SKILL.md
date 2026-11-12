---
name: gemini-web-research
description: >-
  Delegates substantial web research to parallel Gemini workers driven through the agy CLI, and returns reports in
  which every claim is checked against the pages the worker actually read. Use only when the user asks to research
  with Gemini or agy; not for ordinary research requests or a quick search.
license: MIT
compatibility: >-
  Requires the agy CLI (Google Antigravity) installed and logged in, Python 3.9+ (standard library only) and
  network access. Any agent harness with a shell.
---

# Gemini Web Research

You are the research lead. Gemini workers do the searching and reading; you split the request into questions, read
their checked reports and write the answer. Do not search the web or fetch pages yourself, and do not fill gaps from
memory.

## How a round runs

```bash
python3 scripts/gemini_research.py '<question 1>' '<question 2>' '<question 3>'
```

The script path is relative to this skill's directory. One call is one round: each question becomes an independent
`agy` job, all running in parallel. A round takes 3 to 6 minutes. Run it in the background if your harness can;
otherwise run it in the foreground with a timeout of at least 20 minutes, the most a round can take.

Before starting the jobs the script sends `agy` one trivial prompt. If `agy` is missing, or cannot complete that
turn within 90 seconds, the script exits with status 2, starts no job and prints the reason: most often an MCP
server configured in `agy` that never connects, which blocks every print-mode turn. Do not retry. Report the
message to the user: repairing or removing that server is their decision.

Workers run with a minimal `agy` configuration, whatever the user's own settings are: an empty workspace that
holds only the page reader, no slash commands or skills, no MCP tools, no file writes, and no `curl`, `wget`,
`rm`, `sudo`, `ssh` or `git`. `agy --sandbox` is not used, because its terminal has no network.

Each worker must search the web, read the pages it cites and back every claim with a verbatim quote. The script
checks every job against its trace and prints one report per question:

- **FAILED job**: the worker ran no search, read no pages, timed out or returned a malformed report. Nothing from it
  is usable.
- **[OK] claim**: the quote was found in a page the worker read. Usable as a fact.
- **[FLAG] claim**: the URL was never read or the quote is not on the page. Not a fact.
- **Unconfirmed**: things the worker could not find on any page it read.

The model defaults to `gemini-3.8-flash-high`; set `GEMINI_RESEARCH_MODEL` to use another id from `agy models`.

## Pick the tier

Before launching, write one line naming the tier and why. If torn between two, pick the higher. Use exactly these
counts:

| Tier | When | Rounds × jobs |
|---|---|---|
| **Easy** | One fact or a few with an obvious authoritative source: a version, date, price, link, "what is X". | 1 × 2 |
| **Medium** | How something works, a comparison of a few options, a summary across several sources. | 1 × 3 |
| **Hard** | Contested, poorly documented, fast-moving or deeply technical; several linked unknowns; or the answer drives a costly decision. | 2 × 3 |

- **Easy**: job 1 asks the question directly; job 2 asks for the same facts from another angle (for example the
  changelog or package registry instead of the docs), so the answers check each other.
- **Medium**: three different sub-questions that together answer the request.
- **Hard, round 1**: three different sub-questions, like Medium.
- **Hard, round 2**, written after reading round 1: one job on the most important gap or unconfirmed item; one on a
  contradiction between jobs or a flagged claim the answer needs; one that confirms the claim your conclusion rests
  on from a different source.

## Write each question

- **Self-contained.** The worker has none of your context. Name the thing fully and add what disambiguates it: a
  URL, the vendor, the version, the date range.
- **One target per job.** No two jobs in a round cover the same ground.
- **Ask for the specific facts you need**, not "everything about X". Never paste the user's whole request in.

## Read the results

- State as fact only [OK] claims. A [FLAG] claim is a lead, not a fact.
- Rerun a FAILED job once with the same question. If it fails again, report it as failed.
- In an Easy round, compare the two jobs. A disagreement is a gap.
- After an Easy or Medium round, if the answer still depends on a gap, a flagged claim or an unconfirmed item, run
  one more round of exactly one job aimed at it. After a Hard round 2, report remaining gaps as unconfirmed.

## Answer

Give a synthesis, not the raw reports. Link each fact to the URL its [OK] claim came from. Say plainly what stayed
unconfirmed.
