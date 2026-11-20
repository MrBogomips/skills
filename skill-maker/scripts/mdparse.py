"""Minimal Markdown reading for README checks: frontmatter, headings, sections.

Standard library only. Headings inside fenced code blocks are not headings.
"""

import re
from typing import Any, Dict, Iterator, List, Optional, Tuple

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
_CLOSING_HASHES = re.compile(r"(?:^|[ \t]+)#+$")
_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_.-]*):(?:[ \t]+(.*))?$")
_BLOCK_SCALAR = re.compile(r"^[>|][+-]?\d*$")
_LINK = re.compile(r"\]\(\s*(?:<([^>]*)>|([^)\s]+))(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)")
_LINK_DEFINITION = re.compile(r"^ {0,3}\[[^\]]+\]:\s*(?:<([^>]*)>|(\S+))")
_INLINE_CODE = re.compile(r"`+[^`]*`+")


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _fold(style: str, chunks: List[str]) -> str:
    joiner = "\n" if style.startswith("|") else " "
    return joiner.join(chunk.strip() for chunk in chunks if chunk.strip())


def _parse_frontmatter(lines: List[str]) -> Dict[str, str]:
    """Top-level scalars only; nested mappings are kept as an empty string."""
    data = {}
    index = 0
    while index < len(lines):
        match = _KEY.match(lines[index])
        index += 1
        if not match:
            continue
        key, value = match.group(1), (match.group(2) or "").strip()
        chunks = []
        while index < len(lines) and (lines[index][:1] in (" ", "\t") or not lines[index].strip()):
            chunks.append(lines[index])
            index += 1
        if _BLOCK_SCALAR.match(value):
            data[key] = _fold(value, chunks)
        elif value:
            data[key] = _unquote(" ".join([value] + [c.strip() for c in chunks if c.strip()]))
        else:
            data[key] = ""
    return data


def split_frontmatter(text: str) -> Tuple[Optional[Dict[str, str]], List[str], int]:
    """Return (frontmatter dict or None, body lines, 1-based line of the body start)."""
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return None, lines, 1
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return _parse_frontmatter(lines[1:index]), lines[index + 1:], index + 2
    return None, lines, 1


def prose_lines(lines: List[str]) -> Iterator[Tuple[int, str]]:
    """Yield (offset, line) for the lines outside fenced code blocks and multi-line HTML comments."""
    fence = None
    in_comment = False
    for offset, line in enumerate(lines):
        if in_comment:
            in_comment = "-->" not in line
            continue
        match = _FENCE.match(line)
        if fence is None:
            if match:
                fence = match.group(1)
                continue
            if line.lstrip().startswith("<!--") and "-->" not in line:
                in_comment = True
                continue
            yield offset, line
        elif match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence) \
                and not match.group(2).strip():
            fence = None


def headings(lines: List[str], first_line: int = 1) -> List[Dict[str, Any]]:
    """Return the ATX headings outside fences as dicts: level, title, line."""
    found = []
    for offset, line in prose_lines(lines):
        match = _HEADING.match(line)
        if not match:
            continue
        title = _CLOSING_HASHES.sub("", match.group(2) or "").strip()
        found.append({"level": len(match.group(1)), "title": title, "line": first_line + offset})
    return found


def links(lines: List[str], first_line: int = 1) -> List[Dict[str, Any]]:
    """Return link and image targets outside fences and inline code as dicts: target, line."""
    found = []
    for offset, line in prose_lines(lines):
        definition = _LINK_DEFINITION.match(line)
        matches = [definition] if definition else _LINK.finditer(_INLINE_CODE.sub("", line))
        for match in matches:
            found.append({"target": match.group(1) or match.group(2) or "", "line": first_line + offset})
    return found


def _first_paragraph(lines: List[str]) -> str:
    paragraph = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith(("<!--", "#", "```", "~~~")) and not paragraph:
            if stripped.startswith("<!--"):
                continue
            break
        paragraph.append(stripped)
    return " ".join(paragraph)


def parse(text: str) -> Dict[str, Any]:
    """Parse a README into frontmatter, H1s, intro paragraph and H2 sections.

    Each section is a dict: title, line, end (exclusive), h3 (list of headings).
    Line numbers are 1-based and refer to the whole file.
    """
    frontmatter, body, first_line = split_frontmatter(text)
    heads = headings(body, first_line)
    h1s = [h for h in heads if h["level"] == 1]
    last_line = first_line + len(body)
    sections = []
    for head in heads:
        if head["level"] == 2:
            sections.append({"title": head["title"], "line": head["line"], "end": last_line, "h3": []})
        elif head["level"] == 1 and sections:
            sections[-1]["end"] = min(sections[-1]["end"], head["line"])
        elif head["level"] == 3 and sections:
            sections[-1]["h3"].append(head)
    for current, following in zip(sections, sections[1:]):
        current["end"] = min(current["end"], following["line"])
    intro = ""
    if h1s:
        after = [h["line"] for h in heads if h["line"] > h1s[0]["line"]]
        stop = after[0] if after else last_line
        start = h1s[0]["line"] - first_line + 1
        intro = _first_paragraph([line for _, line in prose_lines(body[start: stop - first_line])])
    return {
        "frontmatter": frontmatter,
        "h1": h1s,
        "intro": intro,
        "sections": sections,
        "headings": heads,
        "links": links(body, first_line),
    }
