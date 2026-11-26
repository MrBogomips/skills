---
name: maieutic
description: >-
  Interviews the user about a plan, design or decision in short rounds of questions with recommended answers,
  and logs what was decided and discarded. Use when the user asks to be grilled or interviewed about a plan, to
  stress-test, challenge or poke holes in it, to play devil's advocate, or to settle decisions before acting
  ("grill me", "ask me the hard questions", "put me through the wringer", "play devil's advocate"). Not for ideation
  from scratch, code review, or checking finished work.
license: MIT
compatibility: >-
  Any agent harness. Uses subagents for fact lookups and the harness's question tool when they exist, and falls
  back to plain-text rounds.
metadata:
  minimum-model: Sonnet class or above
---

# Maieutic

Needs a model of Sonnet class or above. On a less capable model, tell the user before going on.

Draw the decisions out of the user through questions, the way Socrates did: the user decides, you find the
facts, recommend, and keep the record. The work is a **design tree**: every decision branches into the decisions
that hang off it. The **frontier** is every open decision whose prerequisites are settled. The **objective** is to reach
a shared understanding and a consensus on the plan.

Two modes:

- **Interview** (default): cooperative. Each question carries your recommendation.
- **Hard**: devil's advocate. On when the user says "hard", `--hard`, "devil's advocate", "poke holes",
  "put me through the wringer" or "no mercy", in any language. Adds the [Hard mode](#hard-mode) rules.

Any other request runs in interview mode, including "grill me" and "stress-test". The user can switch modes at
any time.

Ask in the user's language. Do not act on the plan until the user confirms a shared understanding.

## Before round 1

1. **Read what is under review**: the file, PR, issue or message the user points to. If it is only an idea in
   the conversation, restate it in two or three sentences and let the user correct it.
2. **Read what is already decided**: the project's instruction files (`AGENTS.md`, `CLAUDE.md`), recorded
   decisions (ADRs), and the specs of any spec-driven framework in use. Never ask what they already settle. A
   conflict between the plan and one of them becomes a first-round question that quotes the source.
3. **Create the decision log** (see [Decision log](#decision-log)) with the round-1 questions under **Open**,
   and tell the user its path.

## Rounds

Build each round from the frontier:

1. **Rank** the frontier by cost of being wrong times difficulty of reversing it. Irreversible choices and
   conflicts with recorded decisions come first. Mark one-way doors (data loss, public contracts, commitments
   to third parties) with `(irreversible)`.
2. **Ask at most 5 questions**, `Fact:` questions included. Questions that depend on one still open in this
   round wait for a later round; independent questions are asked together, never one at a time.
3. **Turn cheap, reversible choices into defaults** instead of questions: list them in one line at the end of
   the round. Once the user answers the round without objecting, they go to **Decided**, marked *Default*.
4. **Give every decision question a recommended answer**, so that "yes" accepts it.

Number questions with stable IDs for the whole session: Q1, Q2 and onwards, never restarting and never reused,
so the user can answer "yes to all but 3", "4 B" or "5 no, because …".

A round looks like this:

```markdown
**Round 2** · decided 4 · discarded 2 · open 5

**Q6. Queue technology** — The plan adds RabbitMQ. Options: (A) a jobs table in the existing PostgreSQL;
(B) RabbitMQ, as planned.
→ Recommended: A, because it adds no new service to run.

**Q7. Fact: peak volume** — How many notifications a minute at peak?

Defaults unless you object: 3 retries with backoff; failures go to the existing error log.
```

A fact that only the user can give (a business constraint, a deadline, a measurement only they can run) is
asked as `Fact:` with no recommendation.

### Facts are your job

Before you ask anything, check whether the environment can answer it: files, history, tools, documentation.
Look it up yourself; with a subagent in a fresh context when the harness has one. A lookup in progress blocks
only the questions that depend on it: ask the rest of the frontier now.

### Channel

When the harness offers a question tool that fits the round (a structured-question dialog for a few questions
with discrete options, or a visual board for many interdependent ones), use it, within its limits. Otherwise use
the plain-text format above.

### Answers

| The user says | Record it as |
|---|---|
| "yes", or picks an option | **Decided**, with the reason given or the recommendation's reason |
| rejects an option or the recommendation | the rejected option goes to **Discarded** and their choice to **Decided**, each with its reason |
| "you decide" | **Decided (delegated)**: your recommendation, marked as delegated |
| "don't know", "skip" | **Open**, as an explicit assumption; ask again only when a later decision depends on it |
| an answer you cannot map to one question for certain | nothing yet: state your reading in the next round and ask to confirm |
| "stop", "enough" | end the session now (see [Ending](#ending)) |

After every round, rewrite the log and recompute the frontier. When an answer contradicts a settled decision or
makes it moot, say so and reopen that decision in the next round under its original ID ("Q2 reopened: …").

The decisions are the user's. If they reject your recommendation without new information or a better argument,
say once, briefly, why you still hold it, then record their choice as **Decided** and move on; ask again only
if new facts emerge. When they do bring a better argument, concede explicitly and say what changed your mind.
A choice that overrides a recorded decision or project rule is recorded with "overrides <source>", and the
[Ending](#ending) offers to update that source.

## Hard mode

On top of everything above:

- Before round 1, list the plan's hidden assumptions, and turn the risky ones into questions.
- Every decision question adds a line `Against:` with the strongest case against your own recommendation.
- When the frontier is empty, run one last **pre-mortem** round: "It is six months from now and this failed.
  The likeliest reasons are …": up to 5, each as a question on how to prevent or detect it.

## Decision log

A Markdown file named `<topic>-decisions.md`. Write it where the project's instruction files place working
documents or drafts; otherwise in the session scratchpad, or in the system temporary directory when the harness
has none. Never create a folder in the repository for it. Create it before round 1 and rewrite it after every
answered round, so it survives a compaction of the conversation.

```markdown
# Decisions: <topic>

Reviewed: <file or short description> · Mode: interview | hard · Updated: <date>

## Decided
- **Q1 Queue**: a jobs table in PostgreSQL. No new service to run for a team of three.
- **Q4 Rollout**: behind a flag, tenant by tenant. *Delegated.*

## Discarded
- **Q1 RabbitMQ**: one more system to back up and watch, for a load PostgreSQL handles.
- **Q3 Remove the synchronous path at once**: no fallback if the worker stalls.

## Open
- **Q7 Peak volume**: assumed under 1,000 a minute until the user confirms.
```

Each entry is one line: ID, short title, the decision or the discarded option, and a short rationale. During
the session **Open** holds the questions still unanswered; at the end it holds only what stayed unsettled, as
explicit assumptions. Leave out a section with no entries.

## Ending

The session ends when the frontier is empty (after the pre-mortem in hard mode) or the user stops it. Then:

1. Write the final log and give a short summary: counts of decided, discarded and open items, the most
   consequential decisions, and the log's path.
2. Ask the user to confirm the shared understanding. Until they do, change nothing.
3. Offer the next step without doing it: a revised plan, an implementation plan, a spec in the project's
   framework, an ADR for a decision that deserves one, an update to any source a decision overrides, or a
   handoff if someone else continues.
