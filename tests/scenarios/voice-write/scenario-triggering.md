# Scenario: Description triggering

## Setup
No fixture needed. Run each prompt with `trigger.sh` in a new scratch directory, twice: the first
five prompts give 10 human-facing runs, the last five give 10 excluded runs.

## Invocation
| Prompt | Expected |
|---|---|
| "Scrivi una mail breve al team per dire che il report trimestrale è pronto per la revisione." | `personal-voice:voice-write` |
| "Rédige un court message pour l'équipe : la réunion de lundi est déplacée à 10h." | `personal-voice:voice-write` |
| "Schreib einen kurzen Bericht für meinen Chef über den Stand der Migration." | `personal-voice:voice-write` |
| "Draft an email to our client explaining that the delivery moves to next Tuesday." | `personal-voice:voice-write` |
| "Mi prepari un post LinkedIn per annunciare che sabato parlo al meetup sul testing?" | `personal-voice:voice-write` |
| "Write a commit message for a change that adds a /health endpoint." | not invoked |
| "Scrivi il messaggio di commit per la correzione del bug di login." | not invoked |
| "Write a Python docstring for a function that parses ISO dates." | not invoked |
| "Write a GitHub Actions YAML workflow that runs npm test on push." | not invoked |
| "Explain in two sentences what a mutex is." | not invoked |

## Acceptance Criteria
- [ ] At least 9 of the 10 human-facing runs invoke `personal-voice:voice-write`
- [ ] None of the 10 excluded runs invokes it

Result on 2026-09-29, recorded before the run count was fixed at two per prompt: 10 of 11
human-facing runs invoked the skill (one French run did not); 0 of 5 excluded runs did (one run per
excluded prompt).

## Collisions with the whole marketplace

Run these with `trigger.sh --marketplace` (or `PV_TRIGGER_MARKETPLACE=1`), which loads every plugin
of the repository, twice each. The document skill must win; `personal-voice:voice-write` may also load,
because it defers to the other skill's structure and style.

| Prompt | Expected |
|---|---|
| "Make a client-facing version of the assessment in assessment.md, to send to the customer." | `tech-writing:client-facing-doc` |
| "Write the statement of work for the portal migration from the notes in brief.md." | `project-management:sow-write` |
| "Draft an email to our client explaining that the delivery moves to next Tuesday." | `personal-voice:voice-write`, and no document skill |

- [ ] In every run of the first two prompts, the expected document skill is invoked
- [ ] In at least one of the two runs of the third prompt, `personal-voice:voice-write` is invoked, and no run invokes a tech-writing or project-management skill
- [ ] Record, for each run, whether `personal-voice:voice-write` also loaded; when it did, the Following-the-skill check below applies

Following the skill: when both a document skill and `personal-voice:voice-write` load, the output keeps the
document skill's structure, register and verbatim texts; the profile shows at most in word choice.
