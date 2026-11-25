---
summary: Interviews you about a plan or decision in short rounds of questions with recommended answers, and logs what you decided and what you discarded.
---

# maieutic

`maieutic` interviews you about a plan, design, or decision before you act on it. It asks questions in short rounds, pairing each with a recommended answer, until every decision is settled. You get a decision log recording what you decided and what you explicitly discarded, with a short rationale for each.

## Why

When you read a plan on your own, its weak spots stay hidden: choices nobody made on purpose, conflicts with decisions your project already recorded, and irreversible steps. `maieutic` tackles those first. It looks up the facts it can find, so it asks you only for decisions and for facts you alone know. Each round has at most five questions, and cheap choices become defaults instead of questions. The decision log stays on disk, so it outlives the conversation.

## Installation

```bash
npx skills add MrBogomips/skills --skill maieutic
```

This command installs the same skill included in the `skills` plugin, under the name `maieutic` instead of `skills:maieutic`.

## Usage

Start a session in your own words (such as "grill me about `drafts/plan.md`" or "ask me the hard questions about this plan"), or invoke `/skills:maieutic` with the plugin in Claude Code. Point the skill to a file, a pull request, or an idea in the conversation. A typical question looks like this:

```markdown
**Q6. Queue technology** — The plan adds RabbitMQ. Options: (A) a jobs table in the existing PostgreSQL;
(B) RabbitMQ, as planned.
→ Recommended: A, because it adds no new service to run.
```

- Answer by question ID ("yes to all but 3", "4 B", "5 no, because …"), or say "stop" to end the session.
- Ask for hard mode ("devil's advocate", "poke holes", "no mercy") to add the strongest case against each recommendation and a closing pre-mortem.

Nothing in the plan changes until you confirm the shared understanding.

## Inputs and outputs

`maieutic` reads the plan under review along with your project's recorded decisions: `AGENTS.md`, `CLAUDE.md`, ADRs, and the specs of any spec-driven framework in use. It writes `<topic>-decisions.md` with **Decided** and **Discarded** sections, plus an **Open** section when anything stays unsettled. The file goes where your project's instructions place working documents. Otherwise, it goes to the session scratchpad or the system temporary directory, never to a new folder in the repository.

## Limitations

`maieutic` does not generate ideas from scratch, review code, or check whether work is done. It changes nothing on its own. At the end of a session, it offers a next step, such as a revised plan or an ADR, and waits for you.
