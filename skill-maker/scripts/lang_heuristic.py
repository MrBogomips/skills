"""Heuristic: does a phrase or a text look written in a language other than English?

Standard library only. A warning aid for rule S3, never a verdict: the reviewer confirms each hit.
"""

import re
from typing import Iterable, List

# Short words frequent in Italian, French, German and Spanish and rare as English words.
FOREIGN_WORDS = frozenset("""
il lo gli della delle dello degli di del che non mai così sono fammi sotto questo questa perché anche
le la les des une pour avec est dans sur vous nous pas
der das und nicht ich einen ein ist auf auch
el los las para por una que un
""".split())

ENGLISH_WORDS = frozenset("""
the a an and or of to is are for with when in on at by my me this that it i you your what how too never
not do does be as from if then than so but all any
""".split())

# Accented words that English speakers use as English words.
LOANWORDS = frozenset(["café", "naïve", "naive", "déjà", "résumé", "cliché", "fiancé", "façade", "rôle", "vu"])

_WORD = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*")
_QUOTED = re.compile(r"[\"“]([^\"”\n]{2,160})[\"”]")
_INLINE_CODE = re.compile(r"`+[^`]*`+")
MIN_FOREIGN_IN_TEXT = 5


def _words(text: str) -> List[str]:
    return [word.lower() for word in _WORD.findall(text)]


def _has_foreign_letters(word: str) -> bool:
    return any(not ("a" <= char <= "z") for char in word if char.isalpha()) and word not in LOANWORDS


def phrase_is_foreign(phrase: str) -> bool:
    """A phrase of 2+ words with a foreign function word and no English one, or a foreign-looking letter."""
    words = _words(phrase)
    if any(_has_foreign_letters(word) for word in words):
        return True
    foreign = sum(1 for word in words if word in FOREIGN_WORDS)
    english = sum(1 for word in words if word in ENGLISH_WORDS)
    return len(words) >= 2 and foreign >= 1 and english == 0


def foreign_phrases(text: str) -> List[str]:
    """Return the quoted phrases of `text` (outside inline code) that look foreign."""
    plain = _INLINE_CODE.sub(" ", text)
    return [phrase for phrase in _QUOTED.findall(plain) if phrase_is_foreign(phrase)]


def looks_non_english(lines: Iterable[str]) -> bool:
    """True when foreign function words outnumber English ones in the prose lines given."""
    foreign = english = 0
    for line in lines:
        for word in _words(_INLINE_CODE.sub(" ", line)):
            foreign += word in FOREIGN_WORDS
            english += word in ENGLISH_WORDS
    return foreign >= MIN_FOREIGN_IN_TEXT and foreign > english
