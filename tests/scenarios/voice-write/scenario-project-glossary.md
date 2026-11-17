# Scenario: Project glossary overrides a topic term

## Setup
Fixture created. Working directory: `$F/project`. The topic file prefers "deploy"; the project glossary prefers "rilascio".

## Invocation
"Scrivi una breve mail al team Sportello del cliente: la versione 2.4 è andata in produzione stanotte e da parte loro non serve fare nulla. Cita il rilascio."

## Expected Behavior
- Loads the project glossary after the topic file; the project entry wins
- Audience is the client: `[to clients]` rules apply

## Acceptance Criteria
- [ ] The email uses "rilascio"; "deploy" does not appear
- [ ] The client's back office is called "Sportello", never "backoffice"
- [ ] Closes with "Buona giornata" and uses formal address
- [ ] The answer, when asked, names the topic entry set aside because the project entry took precedence
- [ ] `content-types/status-report.md` is not applied, since a notice email is not a status report

## Edge Cases
- Same request in `$F/plain` → "deploy" (no project store)
- Same request with working directory `$F/project/src` → still "rilascio": the project root comes from `git rev-parse --show-toplevel`, so the store at the root is found
- "Scrivi lo status report settimanale" in `$F/project` → starts with one of "In linea", "A rischio", "In ritardo"
