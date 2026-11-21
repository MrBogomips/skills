#!/usr/bin/env python3
"""Translate text or a file with the Gemini API, in a given target language and register.

Needs an API key in GEMINI_API_KEY (or GOOGLE_API_KEY), sent in the x-goog-api-key
header only. Every call is billed to that key.

    gemini_translate.py --to it -t "Deploy the service and check the logs."
    gemini_translate.py --to de --register formal -i letter.md -o letter.de.md
    gemini_translate.py --to fr --review -i README.md -o README.fr.md

Exit codes: 0 done, 1 error, 2 no API key, 3 source already in the target language,
4 the translation changed code, URLs, placeholders or structure (kept in <output>.unchecked).
Standard library only.
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
DEFAULT_MODEL = "gemini-4-carbon"
KEY_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY")
KEY_SHAPE_RE = re.compile(r"AIza[0-9A-Za-z_-]{20,}")
REGISTERS = ("formal", "professional", "technical", "informal")
DEFAULT_CHUNK_CHARS = 24_000

REFERENCES = Path(__file__).resolve().parent.parent / "references"
STYLE_GUIDE = REFERENCES / "style-guide.md"
LANGUAGES_DIR = REFERENCES / "languages"

LANGUAGE_NAMES = {
    "italian": "it", "italiano": "it", "english": "en", "inglese": "en",
    "german": "de", "deutsch": "de", "tedesco": "de", "french": "fr", "francais": "fr",
    "français": "fr", "francese": "fr", "spanish": "es", "español": "es", "espanol": "es",
    "spagnolo": "es", "portuguese": "pt", "português": "pt", "portoghese": "pt",
    "dutch": "nl", "nederlands": "nl", "japanese": "ja", "chinese": "zh", "korean": "ko",
    "russian": "ru", "polish": "pl", "swedish": "sv", "danish": "da", "norwegian": "no",
    "finnish": "fi", "greek": "el", "turkish": "tr", "arabic": "ar", "hebrew": "he",
    "czech": "cs", "romanian": "ro", "hungarian": "hu", "ukrainian": "uk",
}

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "source_language": {"type": "string",
                            "description": "ISO 639-1 code of the language of the source text."},
        "target_language": {"type": "string",
                            "description": "ISO 639-1 code of the requested target language."},
        "register": {"type": "string", "enum": list(REGISTERS),
                     "description": "The register the translation uses."},
        "translation": {"type": "string",
                        "description": "The complete translated text and nothing else."},
    },
    "required": ["source_language", "target_language", "register", "translation"],
}


# --------------------------------------------------------------------------- #
# Transport and key handling, kept in step with skills/google-image-gen.
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


# --------------------------------------------------------------------------- #
# Prompt assembly.
# --------------------------------------------------------------------------- #
def language_code(language: str) -> str | None:
    """ISO 639-1 code for a code, a locale (pt-BR) or a common language name."""
    value = language.strip().lower()
    head = re.split(r"[-_]", value)[0]
    if re.fullmatch(r"[a-z]{2}", head):
        return head
    return LANGUAGE_NAMES.get(value)


def md_section(text: str, heading: str) -> str:
    """The heading line and body of a Markdown section, up to the next heading of the same or higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        die(f"{heading!r} is missing from {STYLE_GUIDE}; the skill's files are incomplete.")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        match = re.match(r"^(#{1,6})\s", lines[i])
        if match and len(match.group(1)) <= level:
            end = i
            break
    return "\n".join(lines[start:end]).strip()


def language_notes(target: str) -> str:
    code = language_code(target)
    path = LANGUAGES_DIR / f"{code}.md" if code else None
    if not path or not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    first = re.search(r"^## ", text, re.MULTILINE)
    return text[first.start():].strip() if first else ""


def system_instruction(target: str, register: str, *, glossary: str = "",
                       pinned_source: str = "", review: bool = False) -> str:
    guide = STYLE_GUIDE.read_text(encoding="utf-8")
    parts = [md_section(guide, "## Core rules"), f"## Task\n\nTarget language: {target}"]
    if register == "auto":
        parts.append(md_section(guide, "## Registers"))
        parts.append(md_section(guide, "## Register inference"))
    else:
        parts.append(f"Register: {register}")
        parts.append(md_section(guide, f"### {register}"))
    if pinned_source:
        parts.append(f"This text is one part of a longer document. The source language is {pinned_source}. "
                     "Keep terminology, form of address and instruction mood consistent with the rest "
                     "of the document.")
    notes = language_notes(target)
    if notes:
        parts.append(notes)
    if glossary.strip():
        parts.append("## Glossary\n\n" + glossary.strip())
    if review:
        parts.append(md_section(guide, "## Review"))
    return "\n\n".join(parts)


def build_request(model: str, thinking: str, instruction: str, text: str) -> dict:
    return {"model": model, "input": text, "system_instruction": instruction,
            "generation_config": {"thinking_level": thinking},
            "response_format": {"type": "text", "mime_type": "application/json",
                                "schema": RESPONSE_SCHEMA}}


def review_input(source: str, draft: str) -> str:
    return (f"=== SOURCE ===\n{source}\n=== END SOURCE ===\n\n"
            f"=== DRAFT TRANSLATION ===\n{draft}\n=== END DRAFT TRANSLATION ===")


def preview(body: dict, chunks: int) -> str:
    header = f"POST {ENDPOINT}\nApi-Revision: {API_REVISION}\nx-goog-api-key: <not shown>\n"
    if chunks > 1:
        header += f"# first of {chunks} chunks shown\n"
    return header + json.dumps(body, indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# Markdown structure: chunking and invariants.
# --------------------------------------------------------------------------- #
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)")
URL_RE = re.compile(r"\b(?:https?|ftp)://[^\s<>()\[\]\"'`]+[^\s<>()\[\]\"'`.,;:!?]")
PLACEHOLDER_RE = re.compile(r"\{\{\s*[^{}]+?\s*\}\}|\{[A-Za-z_][\w.\-]*\}|%(?:\d+\$)?[sdif]\b|\$\d+\b")
TAG_RE = re.compile(r"</?([A-Za-z][\w-]*)\b[^<>]*>")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s")
TABLE_ROW_RE = re.compile(r"^\s*\|")


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


def outside_fences(text: str) -> list[tuple[int, str]]:
    """(line index, line) for every line that is not inside a fenced code block."""
    return scan_fences(text)[0]


def split_chunks(text: str, limit: int) -> list[str]:
    """Split at headings outside code fences, packing sections up to limit characters."""
    if len(text) <= limit:
        return [text]
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in outside_fences(text) if HEADING_RE.match(line) and i > 0]
    bounds = [0] + starts + [len(lines)]
    sections = ["".join(lines[a:b]) for a, b in zip(bounds, bounds[1:]) if a < b]
    chunks: list[str] = []
    for section in sections:
        if chunks and len(chunks[-1]) + len(section) <= limit:
            chunks[-1] += section
        else:
            chunks.append(section)
    return chunks


def protected(text: str) -> dict[str, Counter]:
    lines, blocks = scan_fences(text)
    prose = "\n".join(line for _, line in lines)
    inline = [m.group(0) for m in INLINE_CODE_RE.finditer(prose)]
    prose = INLINE_CODE_RE.sub(" ", prose)
    return {"code block": Counter(blocks), "inline code": Counter(inline),
            "URL": Counter(URL_RE.findall(prose)),
            "placeholder": Counter(m.group(0) for m in PLACEHOLDER_RE.finditer(prose)),
            "tag": Counter(f"<{'/' if m.group(0).startswith('</') else ''}{m.group(1).lower()}>"
                           for m in TAG_RE.finditer(prose))}


def structure(text: str) -> tuple[list[int], int]:
    lines = outside_fences(text)
    headings = [len(HEADING_RE.match(line).group(1)) for _, line in lines if HEADING_RE.match(line)]
    rows = sum(1 for _, line in lines if TABLE_ROW_RE.match(line))
    return headings, rows


def check_invariants(source: str, translation: str) -> list[str]:
    """Differences in code, URLs, placeholders, tags, headings and table rows."""
    problems = []
    src, out = protected(source), protected(translation)
    for kind in src:
        missing = src[kind] - out[kind]
        extra = out[kind] - src[kind]
        for item in missing:
            problems.append(f"{kind} missing or changed: {shorten(item)}")
        for item in extra:
            problems.append(f"{kind} not in the source: {shorten(item)}")
    (src_heads, src_rows), (out_heads, out_rows) = structure(source), structure(translation)
    if src_heads != out_heads:
        problems.append(f"heading levels differ: source {src_heads}, translation {out_heads}")
    if src_rows != out_rows:
        problems.append(f"table rows differ: source {src_rows}, translation {out_rows}")
    return problems


def shorten(item: str, width: int = 80) -> str:
    flat = " ".join(item.split())
    return flat if len(flat) <= width else flat[:width - 1] + "…"


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
    for field in RESPONSE_SCHEMA["required"]:
        if not isinstance(result, dict) or not isinstance(result.get(field), str):
            die(f"the model's answer lacks the field {field!r}; nothing was written.")
    return result


def keep_trailing_space(source: str, translation: str) -> str:
    """End the translated chunk with as many line breaks as its source chunk, so chunks join cleanly."""
    breaks = source[len(source.rstrip()):].count("\n")
    return translation.rstrip() + "\n" * breaks


def read_source(args: argparse.Namespace) -> str:
    if args.text is not None and args.input is not None:
        die("pass --text or --input, not both.")
    if args.text is not None:
        text = args.text
    elif args.input is not None:
        if not args.input.is_file():
            die(f"input file not found: {args.input}")
        text = args.input.read_text(encoding="utf-8")
    elif sys.stdin.isatty():
        die("nothing to translate: pass --text, --input or pipe the text on stdin.")
    else:
        text = sys.stdin.read()
    if not text.strip():
        die("nothing to translate: the input is empty.")
    return text


def read_glossary(path: Path | None) -> str:
    if path is None:
        return ""
    if not path.is_file():
        die(f"glossary file not found: {path}")
    return path.read_text(encoding="utf-8")


def check_output(out: Path | None) -> None:
    """Fail before spending anything if the output cannot be written."""
    if out is None:
        return
    if out.is_dir():
        die(f"--output is a directory, give a file path: {out}")
    parent = out.parent.resolve()
    while not parent.exists():
        parent = parent.parent
    if not parent.is_dir() or not os.access(parent, os.W_OK):
        die(f"cannot write under {parent}.")


def translate(args: argparse.Namespace, source: str, glossary: str, key: str) -> tuple[str, dict]:
    """Translate chunk by chunk; returns the text and the first chunk's result."""
    register, pinned, first = args.register, "", None
    parts = []
    for chunk in split_chunks(source, args.chunk_chars):
        instruction = system_instruction(args.to, register, glossary=glossary, pinned_source=pinned)
        result = parse_result(call_api(build_request(args.model, args.thinking, instruction, chunk),
                                       key, args.timeout))
        if first is None:
            first = result
            # A target with a region or script (pt-BR, zh-Hant) may convert within one language.
            regional = bool(re.search(r"[-_]", args.to.strip()))
            same = result["source_language"].lower() == result["target_language"].lower()
            if same and not regional:
                die(f"the text is already in the target language ({result['target_language']}); "
                    "nothing was written.", 3)
            register = result["register"] if register == "auto" else register
            pinned = result["source_language"]
        draft = result["translation"]
        if args.review:
            instruction = system_instruction(args.to, register, glossary=glossary,
                                             pinned_source=pinned, review=True)
            body = build_request(args.model, args.thinking, instruction, review_input(chunk, draft))
            draft = parse_result(call_api(body, key, args.timeout))["translation"]
        parts.append(keep_trailing_space(chunk, draft))
    return "".join(parts), {**first, "register": register}


def emit(text: str, out: Path | None) -> None:
    if out is None:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out}")


class Parser(argparse.ArgumentParser):
    """Usage errors exit 1, so exit 2 keeps meaning "no API key"."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        die(message)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = Parser(
        description="Translate text with the Gemini API (billed to your API key).")
    ap.add_argument("--to", required=True, help="Target language: a code (it, pt-BR) or a name (Italian).")
    ap.add_argument("--register", choices=REGISTERS + ("auto",), default="auto",
                    help="Register of the translation (default: inferred from the source).")
    ap.add_argument("-t", "--text", help="Text to translate.")
    ap.add_argument("-i", "--input", type=Path, help="File to translate (default: stdin).")
    ap.add_argument("-o", "--output", type=Path, help="Where to write the translation (default: stdout).")
    ap.add_argument("--glossary", type=Path, help="Terminology file whose mappings override everything else.")
    ap.add_argument("--review", action="store_true",
                    help="Add a revision call per chunk (doubles the cost).")
    ap.add_argument("--model", default=os.environ.get("GEMINI_TRANSLATE_MODEL") or DEFAULT_MODEL,
                    help=f"Model id (default: $GEMINI_TRANSLATE_MODEL or {DEFAULT_MODEL}).")
    ap.add_argument("--thinking", choices=("low", "medium", "high"), default="medium",
                    help="Thinking level sent to the model (default: medium).")
    ap.add_argument("--chunk-chars", type=int, default=DEFAULT_CHUNK_CHARS,
                    help=f"Split longer input at headings into parts of about this size "
                         f"(default: {DEFAULT_CHUNK_CHARS}).")
    ap.add_argument("--timeout", type=int, default=600, help="Seconds per API call (default: 600).")
    ap.add_argument("--print-prompt", action="store_true",
                    help="Print the first request that would be sent (no key) and exit without a call.")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.chunk_chars <= 0:
        die("--chunk-chars must be positive.")
    source = read_source(args)
    glossary = read_glossary(args.glossary)
    if args.print_prompt:
        chunks = split_chunks(source, args.chunk_chars)
        instruction = system_instruction(args.to, args.register, glossary=glossary)
        print(preview(build_request(args.model, args.thinking, instruction, chunks[0]), len(chunks)))
        return
    check_output(args.output)
    key = api_key()
    text, info = translate(args, source, glossary, key)
    inferred = " (inferred)" if args.register == "auto" else ""
    print(f"source: {info['source_language']} · register: {info['register']}{inferred}", file=sys.stderr)
    problems = check_invariants(source, text)
    if problems:
        if args.output:
            kept = args.output.with_name(args.output.name + ".unchecked")
            kept.parent.mkdir(parents=True, exist_ok=True)
            kept.write_text(text, encoding="utf-8")
            where = f"the translation is in {kept}"
        else:
            sys.stdout.write(text if text.endswith("\n") else text + "\n")
            where = "the translation was printed above"
        details = "\n  - ".join(problems)
        die(f"the translation changed protected content ({where}):\n  - {details}", 4)
    emit(text, args.output)


if __name__ == "__main__":
    main()
