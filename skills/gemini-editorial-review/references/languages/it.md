# Italian (it)

Notes added to the system instruction when the text is in Italian. Each `languages/<code>.md` file is named after
the ISO 639-1 code of its language; the script sends everything from its first `##` heading on, and detects the
language with the `Stopwords:` line below (lowercase, space separated).

Stopwords: il lo la gli le di del della dei delle che non per con una uno sono è anche come questo questa più ma nel nella degli alla al ai essere viene può

## Language notes: Italian

Calques and translationese to remove:

- Syntactic and lexical calques from English: *indirizzare un problema* → *affrontare*, *risolvere*;
  *performare* → *funzionare*, *rendere*, *dare buoni risultati*; *fare senso* → *avere senso*; *supportare*
  used for everything → *gestire*, *consentire*, *essere compatibile con*, *sostenere*; *implementare* where
  *realizzare* or *introdurre* is meant; *in termini di*; *assicurarsi di* everywhere.
- Heavy passives: prefer the active voice or the *si passivante*.
- Chains of adverbs in *-mente* and of gerunds.
- Possessives and subject pronouns that Italian drops (*ha alzato la mano*, not *ha alzato la sua mano*).
- Left-branching noun stacks copied from English: unpack them with prepositions.
- False friends: *attualmente* for *actually*, *eventualmente* for *eventually*, *consistente* for *consistent*,
  *realizzare* for *to realize*, *sensibile* for *sensible*.

Bureaucratic filler to cut: *al fine di* (→ *per*), *nell'ottica di*, *si evidenzia che*, *si fa presente che*,
*in data odierna*, *procedere a* + noun, *effettuare* + noun where a verb exists (*effettuare una verifica* →
*verificare*).

LLM tells typical of Italian text:

- *È importante sottolineare che*, *Vale la pena notare che*, *In questo articolo vedremo*, *In conclusione*,
  *In sintesi*, *Ecco* as an opener of every list.
- Inflated words: *fondamentale*, *cruciale*, *robusto*, *potente*, *senza soluzione di continuità*, *a 360
  gradi*, *sfruttare* for *leverage*, *sbloccare* for *unlock*, *viaggio* for a process.
- *Non si tratta solo di X, ma di Y* and *Non X, ma Y* reversals.
- English punctuation: em dashes as connectors (prefer commas, parentheses or a colon), Title Case headings
  (Italian uses sentence case), the serial comma before *e*/*o*.

Typography and conventions:

- Accented capitals written as such (*È*, not *E'*); apostrophes and accents correct (*perché*, *poiché*, *qual
  è*).
- Lowercase for months, days and language names (*lunedì*, *italiano*).
- Quotation marks: « » or " " used consistently; decimal comma and thousands point in running text (*1.250,5*),
  unchanged inside code.
- One form of address throughout (*tu*, *Lei* or *voi*), and for procedures one mood throughout: imperative
  (*Esegui*) or infinitive (*Eseguire*), never both.
- Established English loanwords in technical text are fine (*deploy*, *commit*, *endpoint*, *cache*), used
  invariably and with a consistent gender.
