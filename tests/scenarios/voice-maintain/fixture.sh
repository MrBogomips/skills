#!/usr/bin/env bash
# Layer 2 fixture for personal-voice maintain scenarios: builds a global voice
# store and a git project whose stores hold one case per maintenance scenario;
# or fingerprints them to prove that nothing changes before authorization.
# All content is invented. macOS/BSD compatible (bash 3.2).
set -euo pipefail

GIT_ID=(-c user.name=fixture -c user.email=fixture@example.invalid)

usage() {
    echo "usage: $0 create DIR | fingerprint DIR" >&2
    exit 2
}

write_global() {
    local g="$1"
    mkdir -p "$g/languages" "$g/topics" "$g/exemplars"

    # M-generic: "Write clearly and concisely." adds nothing.
    # M-stale: the rhythm rule was last reinforced 2026-02-10 (over six months).
    cat > "$g/core.md" <<'MD'
---
kind: core
---
## Tone
- Short sentences, one idea each. (evidence: 4, reinforced: 2026-09-02)
- Write clearly and concisely. (evidence: 2, reinforced: 2026-08-10)
- Alternate a long sentence with two short ones in narrative passages. (evidence: 2, reinforced: 2026-02-10)

## Audiences
- [to clients] Formal register, but no bureaucratic formulas. (evidence: 2, reinforced: 2026-07-14)

## Avoid
- Opening pleasantries such as "I hope this email finds you well". (evidence: 5, reinforced: 2026-09-10)
MD

    # M-conflict: the "Lei" rule contradicts the pending "tu with clients" observation.
    cat > "$g/languages/it.md" <<'MD'
---
kind: language
language: it
---
## Audiences
- [it] [to clients] Use "Lei"; close with "Buona giornata". (evidence: 2, reinforced: 2026-08-01)

## Avoid
- [it] "Inoltre" at the start of a sentence; the author starts with "E" or restructures. (evidence: 3, reinforced: 2026-09-05)
MD

    # M-limit: exactly 50 rules, none stale; a pending promotion targets this file.
    {
        printf -- '---\nkind: topic\ntopic: software-engineering\npersonal: false\n'
        printf -- 'description: Professional texts about building and running software\n---\n## Glossary\n'
        local i
        for i in $(seq 1 50); do
            printf -- '- [it] Write "termine-%02d-scelto", not "termine-%02d-evitato". (evidence: 2, reinforced: 2026-0%d-1%d)\n' \
                "$i" "$i" $(( (i % 6) + 4 )) $(( i % 9 ))
        done
    } > "$g/topics/software-engineering.md"

    cat > "$g/observations.md" <<'MD'
---
kind: observations
store: global
last_maintenance: 2026-08-01
---
### Avoid "pertanto"
- kind: lexicon
- language: it
- topic: any
- audience: colleagues
- destination: languages/it.md › Avoid
- evidence: 2
- sources:
  - 2026-09-18 · revision · text: meeting follow-up to the team · "Pertanto, rinviamo la riunione." → "Rinviamo la riunione."
  - 2026-09-25 · spoken correction · text: retrospective reminder to the team · "non uso mai 'pertanto'"

### "Inoltre" at the start of a sentence
- kind: lexicon
- language: it
- topic: any
- audience: colleagues
- destination: languages/it.md › Avoid
- reinforces: languages/it.md › Avoid › "Inoltre" at the start
- evidence: 1
- sources:
  - 2026-09-26 · revision · text: demo announcement to colleagues · "Inoltre, vi chiedo le slide." → "E vi chiedo le slide."

### Use "tu" with clients
- kind: tone
- language: it
- topic: any
- audience: clients
- destination: languages/it.md › Audiences
- evidence: 2
- sources:
  - 2026-09-12 · revision · text: follow-up to a long-standing client contact · "La ringrazio" → "Ti ringrazio"
  - 2026-09-22 · revision · text: meeting recap to the same client team · "Le invio" → "Ti mando"

### Numbered lists for steps
- kind: tone
- language: any
- topic: software-engineering
- audience: colleagues
- destination: core.md › Tone
- evidence: 1
- sources:
  - 2026-05-10 · spoken correction · text: setup guide for new colleagues · "use a numbered list, not bullets, when the order matters"

### "Rollback" instead of "ripristino"
- kind: lexicon
- language: it
- topic: software-engineering
- audience: colleagues
- destination: topics/software-engineering.md › Glossary
- evidence: 2
- sources:
  - 2026-09-03 · revision · text: incident report to the team · "il ripristino della versione" → "il rollback della versione"
  - 2026-09-19 · own text · text: runbook notes · "in caso di errore si fa rollback"

### "Ambiente di test", not "staging"
- kind: lexicon
- language: it
- topic: software-engineering
- audience: colleagues
- destination: topics/software-engineering.md › Glossary
- evidence: 2
- sources:
  - 2026-09-08 · revision · text: release email in an unrelated side project · "in staging" → "in ambiente di test"
  - 2026-09-21 · own text · text: blog post on testing practice · "l'ambiente di test va tenuto pulito"
MD
}

write_project() {
    local repo="$1"
    mkdir -p "$repo/.personal-voice"
    printf '# Example client portal\n' > "$repo/README.md"

    # M-scope: the "ambiente di test" rule also has global evidence from unrelated texts.
    cat > "$repo/.personal-voice/glossary.md" <<'MD'
---
kind: glossary
---
## Terms
- [it] Call the client's back office "Sportello", never "backoffice". (evidence: 2, reinforced: 2026-09-10)
- [it] Write "ambiente di test", not "staging". (evidence: 2, reinforced: 2026-08-28)
MD

    cat > "$repo/.personal-voice/observations.md" <<'MD'
---
kind: observations
store: project
---
MD

    # M-git: the project store is personal (listed in the local exclude file).
    (cd "$repo" && git init -q && printf '.personal-voice/\n' >> .git/info/exclude \
        && git add -A && git "${GIT_ID[@]}" commit -q -m "chore: fixture")
}

create() {
    local dir="$1"
    [[ -e "$dir" ]] && { echo "refusing: $dir exists" >&2; exit 1; }
    mkdir -p "$dir"
    write_global "$dir/store"
    write_project "$dir/project"
    echo "global store: $dir/store"
    echo "project:      $dir/project (personal .personal-voice/)"
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
    fingerprint) fingerprint "$2" ;;
    *) usage ;;
esac
