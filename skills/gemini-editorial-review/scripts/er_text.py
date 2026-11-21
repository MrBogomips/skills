"""Text side of the editorial review: prompt assembly, language detection, answer parsing, invariants.

Shared by every backend: only the transport to the model differs.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

PROFILES = ("technical", "marketing", "professional", "essay", "blog", "creative")
MAX_CHARS = 150_000                  # one call per document; longer texts are split by the user
MIN_STOPWORD_HITS = 5
MIN_STOPWORD_SHARE = 0.12

REFERENCES = Path(__file__).resolve().parent.parent / "references"
GUIDE = REFERENCES / "editorial-guide.md"
LANGUAGES_DIR = REFERENCES / "languages"

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "language": {"type": "string", "description": "ISO 639-1 code of the text's language."},
        "profile": {"type": "string", "enum": list(PROFILES), "description": "The profile applied."},
        "revised": {"type": "string", "description": "The complete revised text and nothing else."},
        "summary": {"type": "array", "items": {"type": "string"},
                    "description": "Three to five short sentences on what changed and what is left."},
    },
    "required": ["language", "profile", "revised", "summary"],
}


class ReviewError(Exception):
    """A failure to report in one line. `code` is the exit status."""

    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.code = code


# --------------------------------------------------------------------------- #
# Markdown scanning.
# --------------------------------------------------------------------------- #
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)")
URL_RE = re.compile(r"\b(?:https?|ftp)://[^\s<>()\[\]\"'`]+[^\s<>()\[\]\"'`.,;:!?]")
PLACEHOLDER_RE = re.compile(r"\{\{\s*[^{}]+?\s*\}\}|\{[A-Za-z_][\w.\-]*\}|%(?:\d+\$)?[sdif]\b|\$\d+\b")
TAG_RE = re.compile(r"</?([A-Za-z][\w-]*)\b[^<>]*>")
FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)
WORD_RE = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)?")


def scan_fences(text: str) -> tuple[list[tuple[int, str]], list[str]]:
    """Lines outside fenced code blocks as (index, line), and each fenced block's text.

    A fence closes on a run of the opener's character at least as long as the opener (CommonMark);
    an unclosed fence runs to the end of the text.
    """
    prose: list[tuple[int, str]] = []
    blocks: list[str] = []
    fence, current = None, []
    for index, line in enumerate(text.splitlines()):
        match = FENCE_RE.match(line)
        if fence:
            current.append(line)
            closing = match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence)
            if closing and not line.strip().lstrip(fence[0]):
                blocks.append("\n".join(current))
                fence, current = None, []
            continue
        if match:
            fence, current = match.group(1), [line]
            continue
        prose.append((index, line))
    if fence:
        blocks.append("\n".join(current))
    return prose, blocks


def prose_text(text: str) -> str:
    return "\n".join(line for _, line in scan_fences(text)[0])


def shorten(item: str, width: int = 80) -> str:
    flat = " ".join(item.split())
    return flat if len(flat) <= width else flat[:width - 1] + "…"


# --------------------------------------------------------------------------- #
# Language detection.
# --------------------------------------------------------------------------- #
def stopword_table() -> dict[str, set[str]]:
    """Stopwords per language code, from the `Stopwords:` line of each languages/<code>.md."""
    table = {}
    for path in sorted(LANGUAGES_DIR.glob("*.md")):
        match = re.search(r"^Stopwords:\s*(.+)$", path.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            table[path.stem] = set(match.group(1).lower().split())
    return table


def detect_language(text: str) -> str | None:
    """The language with notes whose stopwords dominate the prose, or None when unsure."""
    words = [w.lower() for w in WORD_RE.findall(INLINE_CODE_RE.sub(" ", prose_text(text)))]
    if not words:
        return None
    hits = {code: sum(1 for w in words if w in stops) for code, stops in stopword_table().items()}
    ranked = sorted(hits.items(), key=lambda item: item[1], reverse=True)
    if not ranked:
        return None
    best, count = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else 0
    if count < MIN_STOPWORD_HITS or count / len(words) < MIN_STOPWORD_SHARE or count <= runner_up * 1.5:
        return None
    return best


# --------------------------------------------------------------------------- #
# Prompt assembly.
# --------------------------------------------------------------------------- #
def md_section(text: str, heading: str) -> str:
    """The heading line and body of a Markdown section, up to the next heading of the same or higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == heading), None)
    if start is None:
        raise ReviewError(f"{heading!r} is missing from {GUIDE}; the skill's files are incomplete.")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        match = re.match(r"^(#{1,6})\s", lines[i])
        if match and len(match.group(1)) <= level:
            end = i
            break
    return "\n".join(lines[start:end]).strip()


def language_notes(code: str | None) -> str:
    path = LANGUAGES_DIR / f"{code}.md" if code else None
    if not path or not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    first = re.search(r"^## ", text, re.MULTILINE)
    return text[first.start():].strip() if first else ""


def system_instruction(profile: str, *, lang: str | None, audience: str = "",
                       rules: list[tuple[str, str]] | None = None, glossary: str = "") -> str:
    guide = GUIDE.read_text(encoding="utf-8")
    parts = [md_section(guide, "## Core rules"), md_section(guide, "## LLM tells"),
             md_section(guide, "## Workflow")]
    task = ["## Task"]
    if profile == "auto":
        parts += [md_section(guide, "## Profiles"), md_section(guide, "## Profile inference")]
    else:
        task.append(f"Profile: {profile}")
        parts.append(md_section(guide, f"### {profile}"))
    if audience.strip():
        task.append(f"Audience: {audience.strip()}")
    if len(task) > 1:
        parts.append("\n\n".join(task))
    notes = language_notes(lang)
    if notes:
        parts.append(notes)
    if rules:
        house = [md_section(guide, "## House rules")]
        house += [f"### From {name}\n\n{text.strip()}" for name, text in rules if text.strip()]
        parts.append("\n\n".join(house))
    if glossary.strip():
        parts.append("## Glossary\n\n" + glossary.strip())
    return "\n\n".join(parts)


# --------------------------------------------------------------------------- #
# The model's answer.
# --------------------------------------------------------------------------- #
def parse_answer(raw: str) -> dict:
    """The JSON answer the schema asks for, checked field by field."""
    raw = re.sub(r"^```(?:json)?\s*\n(.*)\n```$", r"\1", raw.strip(), flags=re.DOTALL)
    try:
        result = json.loads(raw)
    except ValueError:
        raise ReviewError("the model did not return the expected JSON: " + shorten(raw, 300)) from None
    if not isinstance(result, dict):
        raise ReviewError("the model's answer is not a JSON object; nothing was written.")
    for field in ("language", "profile", "revised"):
        if not isinstance(result.get(field), str):
            raise ReviewError(f"the model's answer lacks the field {field!r}; nothing was written.")
    summary = result.get("summary")
    if not isinstance(summary, list) or not all(isinstance(line, str) for line in summary):
        raise ReviewError("the model's answer lacks a 'summary' list of sentences; nothing was written.")
    return result


# --------------------------------------------------------------------------- #
# Invariants.
# --------------------------------------------------------------------------- #
def protected(text: str) -> dict[str, Counter]:
    lines, blocks = scan_fences(text)
    prose = "\n".join(line for _, line in lines)
    inline = [m.group(0) for m in INLINE_CODE_RE.finditer(prose)]
    prose = INLINE_CODE_RE.sub(" ", prose)
    frontmatter = FRONTMATTER_RE.match(text)
    return {"code block": Counter(blocks), "inline code": Counter(inline),
            "URL": Counter(URL_RE.findall(prose)),
            "placeholder": Counter(m.group(0) for m in PLACEHOLDER_RE.finditer(prose)),
            "tag": Counter(f"<{'/' if m.group(0).startswith('</') else ''}{m.group(1).lower()}>"
                           for m in TAG_RE.finditer(prose)),
            "frontmatter": Counter([frontmatter.group(1)] if frontmatter else [])}


def check_invariants(source: str, revised: str) -> list[str]:
    """Differences in code, URLs, placeholders, tags and frontmatter. Headings and tables may change."""
    problems = []
    src, out = protected(source), protected(revised)
    for kind in src:
        for item in src[kind] - out[kind]:
            problems.append(f"{kind} missing or changed: {shorten(item)}")
        for item in out[kind] - src[kind]:
            problems.append(f"{kind} not in the source: {shorten(item)}")
    return problems
