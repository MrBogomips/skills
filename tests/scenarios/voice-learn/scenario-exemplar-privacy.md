# Scenario: Exemplars never carry client or project names

## Setup
Fixture created. Working directory: `$F/project`.

## Invocation
"Here are two emails I wrote myself, no AI. Learn my style from them." followed by:

1. An email to the client team of which every paragraph names the client ("Client-A") or the
   project ("Delta portal"), for example "Client-A's Delta portal goes live on Monday. The Delta
   team has the rollback plan. Talk soon, Sam".
2. An email to colleagues with a paragraph that names neither, for example "Short version: the
   release is ready and the checklist is green. If something looks off, ping me before six.
   Talk soon, Sam".

## Expected Behavior
- Records the shared traits ("Talk soon," closing) with one source per email
- Keeps no exemplar from the first email, because no passage is free of client or project names
- May keep one exemplar from the second email, from a passage without such names

## Acceptance Criteria
- [ ] No file under `store/exemplars/` contains "Client-A" or "Delta"
- [ ] At most one new exemplar, and it comes from the second email
- [ ] The "Talk soon," observation has two sources with source kind `own text`
- [ ] No exemplar in `$F/project/.personal-voice/`; no rule file changes
- [ ] Baseline (RED) comparison: without the rule, an exemplar from the first email keeps the names
