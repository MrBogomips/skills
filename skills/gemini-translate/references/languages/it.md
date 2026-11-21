# Italian (it)

Notes added to the system instruction when the target language is Italian. Each `languages/<code>.md` file is
named after the ISO 639-1 code of its language; the script sends everything from its first `##` heading on.

## Target language notes: Italian

Form of address per register:

- `formal`: *Lei*, or impersonal constructions. Formal connectors where useful (*pertanto*, *tuttavia*, *in
  conformità con*).
- `professional`: *Lei* for one person, *voi* for a team or a company. No *burocratese*: avoid *spettabile*, *la
  presente per*, *codesto*, *si prega di voler*.
- `technical`: imperative (*Seleziona*, *Esegui*) or infinitive (*Selezionare*, *Eseguire*) for procedures, never
  both in the same document; impersonal *si* for system behavior.
- `informal`: *tu*.

Calques to avoid:

- English passives: prefer the active voice or the *si passivante* (*si prevede che*, not *ci si aspetta che* or
  *è previsto da*).
- Noun stacks: unpack left-branching chains (*user authentication token expiration policy* → *criterio di
  scadenza del token di autenticazione dell'utente*).
- False friends: *actually* → *in realtà*, *eventually* → *alla fine*, *consistent* → *coerente*, *library* →
  *libreria* (software) or *biblioteca*, *to provide* → *fornire*/*offrire*, *to realize* → *rendersi conto*,
  *sensible* → *sensato*, *argument* → *discussione* or *argomento* (function parameter).
- Possessives and subject pronouns: Italian drops most of them (*ha alzato la mano*, not *ha alzato la sua
  mano*; *Esegui il comando*, not *Tu esegui il comando*).
- Gerund chains and *-mente* adverbs stacked one after another.

Typography:

- No serial (Oxford) comma before *e*/*o*.
- Fewer em dashes than English: prefer commas, parentheses or a colon.
- Quotation marks: « » or " " consistently; decimal comma and thousands point in running text (*1.250,5*),
  unchanged inside code.
- Accented capitals written as such (*È*, not *E'*).
- Lowercase for months, days and language names (*lunedì*, *italiano*).
- Headings in sentence case, not English title case.
