#!/usr/bin/env python3
"""Editorial review of a text, in its own language, with the Gemini API.

Needs an API key in GEMINI_API_KEY (or GOOGLE_API_KEY), sent in the x-goog-api-key
header only. Every call is billed to that key: one call per document.

    gemini_editorial_review.py -i draft.md -o draft.reviewed.md
    gemini_editorial_review.py --profile technical --rules docs/style.md -i README.md -o README.reviewed.md

Exit codes: 0 done, 1 error, 2 no API key, 4 the revision changed code, URLs, placeholders,
tags or the frontmatter (kept in <output>.unchecked). Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import ssl
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
API_REVISION = "2026-05-20"          # sent as Api-Revision, as in the Gemini API docs
DEFAULT_MODEL = "gemini-4-neon"
MODEL_ENV = "GEMINI_EDITORIAL_MODEL"
# Gemini 4 tiers in ascending order; the skill is meant for Neon or above.
MODEL_RANK = ("hydrogen", "carbon", "neon", "argon")
MIN_TIER = "neon"
KEY_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY")
KEY_SHAPE_RE = re.compile(r"AIza[0-9A-Za-z_-]{20,}")
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


# --------------------------------------------------------------------------- #
# Transport and key handling, kept in step with skills/gemini-translate.
# --------------------------------------------------------------------------- #
def die(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


def api_key() -> str:
    for name in KEY_VARS:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    die("no API key: set GEMINI_API_KEY (or GOOGLE_API_KEY) to your Gemini API key.", 2)


def scrub(text: str, key: str = "") -> str:
    """Remove the key, and anything shaped like one, from text that may be echoed."""
    if key:
        text = text.replace(key, "***")
    return KEY_SHAPE_RE.sub("***", text)


def http_failure(code: int, detail: str) -> str:
    detail = f": {detail}" if detail else ""
    if code in (401, 403):
        return (f"the API key was rejected or lacks access (HTTP {code}){detail}. "
                "Check GEMINI_API_KEY and that its project may use this model.")
    if code == 400:
        return (f"the request was rejected (HTTP 400){detail}. An unknown model id is the "
                "usual cause: list the models with GET /v1beta/models and pass --model.")
    if code == 402:
        return (f"the project behind the API key has no credit left (HTTP 402){detail} "
                "Top up or enable billing in Google AI Studio; nothing was billed.")
    if code == 429:
        return f"rate limit or quota exceeded (HTTP 429){detail}. Wait and retry later."
    if code >= 500:
        return f"the Gemini service failed (HTTP {code}){detail}"
    return f"unexpected HTTP {code}{detail}"


def error_detail(exc: urllib.error.HTTPError, key: str) -> str:
    try:
        payload = json.loads(exc.read().decode("utf-8", "replace"))
        # The Interactions endpoint wraps the error object in a one-element array.
        if isinstance(payload, list) and payload:
            payload = payload[0]
        message = payload["error"]["message"]
    except (ValueError, KeyError, TypeError, OSError):
        message = exc.reason if isinstance(exc.reason, str) else ""
    return scrub(" ".join(str(message).split())[:300], key)


def ssl_context() -> ssl.SSLContext:
    """Default verification; some Python builds on macOS ship without CA certificates."""
    ctx = ssl.create_default_context()
    system_bundle = "/etc/ssl/cert.pem"
    if not ctx.cert_store_stats().get("x509_ca") and os.path.isfile(system_bundle):
        ctx = ssl.create_default_context(cafile=system_bundle)
    return ctx


def post_once(body: dict, key: str, timeout: int) -> dict:
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": key,
                 "Api-Revision": API_REVISION})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_api(body: dict, key: str, timeout: int) -> dict:
    """POST once; retry a single time on a 5xx or a timeout. Exits with one line on failure."""
    for attempt in (1, 2):
        try:
            return post_once(body, key, timeout)
        except urllib.error.HTTPError as exc:
            if exc.code >= 500 and attempt == 1:
                continue
            die(http_failure(exc.code, error_detail(exc, key)))
        except (socket.timeout, TimeoutError):
            if attempt == 1:
                continue
            die(f"the Gemini API timed out twice ({timeout}s each); nothing was written.")
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (socket.timeout, TimeoutError)) and attempt == 1:
                continue
            die(f"could not reach the Gemini API: {scrub(str(exc.reason), key)}")
        except ValueError:
            die("the Gemini API returned a response that is not JSON.")
    return {}


def model_warning(model: str) -> str:
    """A warning when a Gemini 4 model below Neon is chosen; other ids pass silently."""
    match = re.fullmatch(r"(?:models/)?gemini-4-([a-z]+)", model.strip())
    if not match or match.group(1) not in MODEL_RANK:
        return ""
    if MODEL_RANK.index(match.group(1)) >= MODEL_RANK.index(MIN_TIER):
        return ""
    return (f"{model} is below gemini-4-{MIN_TIER}: expect a flatter voice and more calques. "
            f"Use gemini-4-{MIN_TIER} or gemini-4-argon for editorial work.")


# --------------------------------------------------------------------------- #
# Markdown scanning: language detection and invariants.
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


def shorten(item: str, width: int = 80) -> str:
    flat = " ".join(item.split())
    return flat if len(flat) <= width else flat[:width - 1] + "…"


# --------------------------------------------------------------------------- #
# Prompt assembly.
# --------------------------------------------------------------------------- #
def md_section(text: str, heading: str) -> str:
    """The heading line and body of a Markdown section, up to the next heading of the same or higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        die(f"{heading!r} is missing from {GUIDE}; the skill's files are incomplete.")
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


def build_request(model: str, thinking: str, instruction: str, text: str) -> dict:
    return {"model": model, "input": text, "system_instruction": instruction,
            "generation_config": {"thinking_level": thinking},
            "response_format": {"type": "text", "mime_type": "application/json",
                                "schema": RESPONSE_SCHEMA}}


def preview(body: dict) -> str:
    header = f"POST {ENDPOINT}\nApi-Revision: {API_REVISION}\nx-goog-api-key: <not shown>\n"
    return header + json.dumps(body, indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# Response handling and the run.
# --------------------------------------------------------------------------- #
def parse_result(data: dict) -> dict:
    texts = [block["text"] for step in data.get("steps") or [] if step.get("type") == "model_output"
             for block in step.get("content") or [] if block.get("type") == "text" and block.get("text")]
    if not texts:
        status = data.get("status") or "unknown"
        die(f"the response held no text (status: {status}); the text may have been blocked by a "
            "safety filter. Nothing was written.")
    raw = "".join(texts).strip()
    raw = re.sub(r"^```(?:json)?\s*\n(.*)\n```$", r"\1", raw, flags=re.DOTALL)
    try:
        result = json.loads(raw)
    except ValueError:
        die("the model did not return the expected JSON: " + shorten(raw, 300))
    if not isinstance(result, dict):
        die("the model's answer is not a JSON object; nothing was written.")
    for field in ("language", "profile", "revised"):
        if not isinstance(result.get(field), str):
            die(f"the model's answer lacks the field {field!r}; nothing was written.")
    summary = result.get("summary")
    if not isinstance(summary, list) or not all(isinstance(line, str) for line in summary):
        die("the model's answer lacks a 'summary' list of sentences; nothing was written.")
    return result


def read_file(path: Path, what: str) -> str:
    if not path.is_file():
        die(f"{what} file not found: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        die(f"cannot read {what} file {path}: {exc}")
    return ""


def read_source(args: argparse.Namespace) -> str:
    if args.text is not None and args.input is not None:
        die("pass --text or --input, not both.")
    if args.text is not None:
        text = args.text
    elif args.input is not None:
        text = read_file(args.input, "input")
    elif sys.stdin.isatty():
        die("nothing to review: pass --text, --input or pipe the text on stdin.")
    else:
        text = sys.stdin.read()
    if not text.strip():
        die("nothing to review: the input is empty.")
    if len(text) > MAX_CHARS:
        die(f"the text has {len(text)} characters, more than {MAX_CHARS} for one call: split the "
            "document (by chapter or section) and review each part.")
    return text


def check_output(out: Path | None, source: Path | None) -> None:
    """Fail before spending anything if the output cannot be written or would replace the source."""
    if out is None:
        return
    if source is not None and out.resolve() == source.resolve():
        die("--output is the input file: the skill never overwrites the source. Choose another path.")
    if out.is_dir():
        die(f"--output is a directory, give a file path: {out}")
    parent = out.parent.resolve()
    while not parent.exists():
        parent = parent.parent
    if not parent.is_dir() or not os.access(parent, os.W_OK):
        die(f"cannot write under {parent}.")


def emit(text: str, out: Path | None) -> None:
    if out is None:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out}")


def report(result: dict, inferred: bool) -> None:
    mark = " (inferred)" if inferred else ""
    print(f"language: {result['language']} · profile: {result['profile']}{mark}", file=sys.stderr)
    for line in result["summary"]:
        print(f"- {line.strip()}", file=sys.stderr)


def keep_unchecked(text: str, out: Path | None, problems: list[str]) -> None:
    if out:
        kept = out.with_name(out.name + ".unchecked")
        kept.parent.mkdir(parents=True, exist_ok=True)
        kept.write_text(text, encoding="utf-8")
        where = f"the revision is in {kept}"
    else:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")
        where = "the revision was printed above"
    details = "\n  - ".join(problems)
    die(f"the revision changed protected content ({where}):\n  - {details}", 4)


class Parser(argparse.ArgumentParser):
    """Usage errors exit 1, so exit 2 keeps meaning "no API key"."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        die(message)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = Parser(description="Editorial review of a text, in its own language, with the Gemini API "
                            "(billed to your API key).")
    ap.add_argument("-t", "--text", help="Text to review.")
    ap.add_argument("-i", "--input", type=Path, help="File to review (default: stdin).")
    ap.add_argument("-o", "--output", type=Path, help="Where to write the revision (default: stdout).")
    ap.add_argument("--profile", choices=PROFILES + ("auto",), default="auto",
                    help="Kind of text (default: inferred).")
    ap.add_argument("--audience", default="", help="Who reads the text, in a few words.")
    ap.add_argument("--rules", type=Path, action="append", default=[],
                    help="House rules file (style guide, writing rules); repeatable, later files win.")
    ap.add_argument("--glossary", type=Path, help="Terminology file whose terms must be kept.")
    ap.add_argument("--lang", help="Language code whose notes to send (default: detected).")
    ap.add_argument("--model", default=os.environ.get(MODEL_ENV) or DEFAULT_MODEL,
                    help=f"Model id (default: ${MODEL_ENV} or {DEFAULT_MODEL}).")
    ap.add_argument("--thinking", choices=("low", "medium", "high"), default="high",
                    help="Thinking level sent to the model (default: high).")
    ap.add_argument("--timeout", type=int, default=900, help="Seconds per API call (default: 900).")
    ap.add_argument("--print-prompt", action="store_true",
                    help="Print the request that would be sent (no key) and exit without a call.")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    rules = [(path.name, read_file(path, "rules")) for path in args.rules]
    glossary = read_file(args.glossary, "glossary") if args.glossary else ""
    source = read_source(args)
    warning = model_warning(args.model)
    if warning:
        print(f"WARNING: {warning}", file=sys.stderr)
    lang = args.lang.strip().lower().split("-")[0] if args.lang else detect_language(source)
    instruction = system_instruction(args.profile, lang=lang, audience=args.audience,
                                     rules=rules, glossary=glossary)
    body = build_request(args.model, args.thinking, instruction, source)
    if args.print_prompt:
        print(preview(body))
        return
    check_output(args.output, args.input)
    key = api_key()
    result = parse_result(call_api(body, key, args.timeout))
    report(result, args.profile == "auto")
    problems = check_invariants(source, result["revised"])
    if problems:
        keep_unchecked(result["revised"], args.output, problems)
    emit(result["revised"], args.output)


if __name__ == "__main__":
    main()
