# Scenario: Session started in a subdirectory of the project

## Setup
Fixture created. Working directory: `$F/project/src` (a subdirectory of the git project whose
root holds `.personal-voice/`). Session so far: Claude wrote for the client team "Il deploy della
versione 2.5 è previsto per venerdì. Buona giornata".

## Invocation
"L'ho mandata cambiando 'Il deploy' in 'Il rilascio in Sportello': è il loro nome per il back office."

## Expected Behavior
- Finds the project root with `git rev-parse --show-toplevel`, without a permission prompt
- Records the project term in the existing store at the root, `$F/project/.personal-voice/`
- Does not offer to create a project store, and creates nothing under `src/`

## Acceptance Criteria
- [ ] The observation for the client's term is in `$F/project/.personal-voice/observations.md`, and its source carries no `project:` tag (a project-store source never does)
- [ ] `$F/project/src/.personal-voice/` does not exist
- [ ] No project-store initialization question is asked
- [ ] The notice line names the project store as the destination
- [ ] Live run (plugin loaded, `--permission-mode default`): `git rev-parse --show-toplevel` is not denied and asks for no permission

## Edge Cases
- The same revision with working directory `$F/plain/sub` (outside git, no store; create it with `mkdir -p`) → the working directory is the root; the skill offers the project store for `$F/plain/sub` only after the author confirms, with no git explanation
- personal-voice:voice-write with working directory `$F/project/src` → reads the root glossary ("rilascio" wins over "deploy"); see scenario-project-glossary.md in voice-write
