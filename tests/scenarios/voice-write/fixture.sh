#!/usr/bin/env bash
# Layer 2 fixture for personal-voice write and learn scenarios: builds a
# disposable global voice store, a git project with a project store, and a
# plain directory with no project store; or fingerprints them to detect writes.
# All content is invented. macOS/BSD compatible (bash 3.2).
set -euo pipefail

GIT_ID=(-c user.name=fixture -c user.email=fixture@example.invalid)

usage() {
    echo "usage: $0 create DIR | create-empty DIR | fingerprint DIR" >&2
    exit 2
}

write_global() {
    local g="$1"
    mkdir -p "$g/languages" "$g/topics" "$g/exemplars"

    cat > "$g/core.md" <<'MD'
---
kind: core
---
## Tone
- Short sentences, one idea each. (evidence: 4, reinforced: 2026-09-02)
- State the point in the first sentence; no warm-up paragraph. (evidence: 3, reinforced: 2026-08-20)

## Audiences
- [to clients] Formal register, but no bureaucratic formulas. (evidence: 2, reinforced: 2026-07-14)

## Avoid
- Opening pleasantries such as "I hope this email finds you well" or their equivalents in any language. (evidence: 5, reinforced: 2026-09-10)
- A closing paragraph that summarizes what the text already said. (evidence: 3, reinforced: 2026-08-28)
MD

    cat > "$g/languages/it.md" <<'MD'
---
kind: language
language: it
---
## Tone
- [it] Use the colon to introduce the point instead of "ovvero". (evidence: 2, reinforced: 2026-06-30)

## Audiences
- [it] [to colleagues] Use "tu"; close with "Un saluto e a presto", never "Cordiali saluti". (evidence: 3, reinforced: 2026-09-12)
- [it] [to clients] Use "Lei"; close with "Buona giornata". (evidence: 2, reinforced: 2026-08-01)

## Avoid
- [it] "Inoltre" at the start of a sentence; the author starts with "E" or restructures. (evidence: 3, reinforced: 2026-09-05)

## Signature expressions
- [it] "Detto fatto" to report that a requested action is complete. (evidence: 2, reinforced: 2026-07-22)
MD

    cat > "$g/languages/en.md" <<'MD'
---
kind: language
language: en
---
## Tone
- [en] Use contractions ("it's", "we'll") except in contracts and formal reports. (evidence: 2, reinforced: 2026-05-18)

## Avoid
- [en] "Delve", "leverage" as a verb, "seamless". (evidence: 3, reinforced: 2026-08-11)
MD

    cat > "$g/topics/software-engineering.md" <<'MD'
---
kind: topic
topic: software-engineering
personal: false
description: Professional texts about building and running software
---
## Glossary
- [it] Write "deploy", not "rilascio", for putting a version in production. (evidence: 2, reinforced: 2026-09-01)
- [it] Write "ambiente di test", not "staging". (evidence: 2, reinforced: 2026-08-15)

## Preferred expressions
- [it] "Va in produzione" rather than "viene rilasciato in produzione". (evidence: 2, reinforced: 2026-08-15)
MD

    cat > "$g/topics/cycling.md" <<'MD'
---
kind: topic
topic: cycling
personal: false
description: Road cycling as a hobby, club outings and training
---
## Glossary
- [it] Call a group ride an "uscita", never a "giro". (evidence: 2, reinforced: 2026-09-14)

## Borrowed expressions
- [it] "Chapeau" to praise a strong ride. (evidence: 2, reinforced: 2026-09-14)
MD

    cat > "$g/topics/family.md" <<'MD'
---
kind: topic
topic: family
personal: true
description: Messages to relatives
---
## Glossary
- [it] Sign messages to relatives with the nickname "Teo". (evidence: 2, reinforced: 2026-09-20)
MD

    cat > "$g/exemplars/software-engineering.it.01.md" <<'MD'
---
kind: exemplar
topic: software-engineering
language: it
audience: colleagues
source: status email to the team
added: 2026-06-10
words: 62
---
Ciao a tutti,

la 4.1 è in ambiente di test da stamattina. Due cose da sapere: il login via
SSO è ancora disattivato e i report notturni partono alle 3, non alle 2.

Se entro giovedì non emergono problemi, facciamo il deploy venerdì mattina.
Chi ha dubbi mi scriva oggi.

Un saluto e a presto
MD

    cat > "$g/exemplars/software-engineering.en.01.md" <<'MD'
---
kind: exemplar
topic: software-engineering
language: en
audience: clients
source: release note to a client
added: 2026-05-02
words: 48
---
Version 3.2 is live. Two changes affect your team: exports now run in the
background, and the audit log keeps 24 months instead of 12.

Nothing to do on your side. If exports look slower than usual this week,
tell us and we'll check the queue.
MD

    cat > "$g/observations.md" <<'MD'
---
kind: observations
store: global
last_maintenance: 2026-09-01
---
### Avoid "pertanto"
- kind: lexicon
- language: it
- topic: any
- audience: colleagues
- destination: languages/it.md › Avoid
- evidence: 1
- sources:
  - 2026-09-18 · revision · text: meeting follow-up to the team · "Pertanto, rinviamo la riunione." → "Rinviamo la riunione."

### Numbered lists for steps
- kind: tone
- language: any
- topic: software-engineering
- audience: colleagues
- destination: core.md › Tone
- evidence: 1
- sources:
  - 2026-09-20 · spoken correction · text: setup guide for new colleagues · "use a numbered list, not bullets, when the order matters"
MD
}

write_project() {
    local repo="$1"
    mkdir -p "$repo/src" "$repo/.personal-voice/content-types"
    printf '# Example client portal\n\nInternal project.\n' > "$repo/README.md"
    printf 'print("hello")\n' > "$repo/src/app.py"

    cat > "$repo/.personal-voice/glossary.md" <<'MD'
---
kind: glossary
---
## Terms
- [it] Use "rilascio", not "deploy", for a production release; the client's term. (evidence: 2, reinforced: 2026-09-10)
- [it] Call the client's back office "Sportello", never "backoffice". (evidence: 2, reinforced: 2026-09-10)
MD

    cat > "$repo/.personal-voice/content-types/status-report.md" <<'MD'
---
kind: content-type
content_type: status-report
---
## Conventions
- Start with a one-line status: "In linea", "A rischio" or "In ritardo". (evidence: 2, reinforced: 2026-09-03)
MD

    cat > "$repo/.personal-voice/observations.md" <<'MD'
---
kind: observations
store: project
---
MD

    (cd "$repo" && git init -q && printf '.personal-voice/\n' >> .git/info/exclude \
        && git add -A && git "${GIT_ID[@]}" commit -q -m "chore: fixture")
}

create() {
    local dir="$1"
    [[ -e "$dir" ]] && { echo "refusing: $dir exists" >&2; exit 1; }
    mkdir -p "$dir"
    write_global "$dir/store"
    write_project "$dir/project"
    mkdir -p "$dir/plain"
    echo "global store: $dir/store"
    echo "project:      $dir/project (has .personal-voice/)"
    echo "plain dir:    $dir/plain (no project store, not git)"
}

create_empty() {
    local dir="$1"
    [[ -e "$dir" ]] && { echo "refusing: $dir exists" >&2; exit 1; }
    mkdir -p "$dir/store" "$dir/plain"
    echo "empty global store: $dir/store"
    echo "plain dir:          $dir/plain"
}

fingerprint() {
    local dir="$1"
    (cd "$dir" && find . -type f -not -path '*/.git/objects/*' -not -path '*/.git/logs/*' \
        -not -name index -not -name ORIG_HEAD | LC_ALL=C sort | while IFS= read -r f; do
            printf '%s  %s\n' "$(cksum < "$f" | awk '{print $1}')" "$f"
        done)
}

[[ $# -eq 2 ]] || usage
case "$1" in
    create) create "$2" ;;
    create-empty) create_empty "$2" ;;
    fingerprint) fingerprint "$2" ;;
    *) usage ;;
esac
