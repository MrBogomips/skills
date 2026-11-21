#!/usr/bin/env python3
"""Editorial review of a text, in its own language, by Gemini through the local agy CLI or the Gemini API.

    gemini_editorial_review.py -i draft.md -o draft.reviewed.md
    gemini_editorial_review.py --via api --profile technical --rules docs/style.md -i README.md -o README.reviewed.md
    gemini_editorial_review.py config [show]
    gemini_editorial_review.py config set backend agy [--project]
    gemini_editorial_review.py config unset backend [--project]

Backends: `agy` runs one turn of the Antigravity CLI on the user's agy login; `api` calls the Gemini API
with GEMINI_API_KEY, billed to that key. `auto` (the default) picks agy when it is installed.
Settings come from er_config: user file, project file, environment, then flags.

Exit codes: 0 done, 1 error, 2 the backend is unavailable (no API key, agy missing or unable to start
a turn), 4 the revision changed code, URLs, placeholders, tags or the frontmatter (kept in
<output>.unchecked). Standard library only.
"""
from __future__ import annotations

import argparse
import os
import re
import signal
import sys
from pathlib import Path

import er_agy
import er_api
import er_config
from er_text import (MAX_CHARS, PROFILES, ReviewError, check_invariants, detect_language,
                     system_instruction)

MODEL_ENV = "GEMINI_EDITORIAL_MODEL"
# Gemini 4 tiers in ascending order; the skill is meant for Neon or above.
MODEL_RANK = ("hydrogen", "carbon", "neon", "argon")
MIN_TIER = "neon"


def model_warning(model: str) -> str:
    """Why the chosen model is a poor fit for editorial work, or an empty string."""
    name = re.sub(r"^models/", "", model.strip())
    advice = f"Use gemini-4-{MIN_TIER} or gemini-4-argon for editorial work."
    if not name.startswith("gemini-"):
        return (f"{model} is not a Gemini model: the review is meant to come from a different model "
                f"than the one that wrote the text. {advice}")
    tier = re.fullmatch(r"gemini-4-([a-z]+)(?:-[a-z]+)?", name)
    if tier and tier.group(1) in MODEL_RANK:
        if MODEL_RANK.index(tier.group(1)) >= MODEL_RANK.index(MIN_TIER):
            return ""
        return f"{model} is below gemini-4-{MIN_TIER}: expect a flatter voice and more calques. {advice}"
    if re.match(r"gemini-[0-3](?:[.-]|$)", name):
        return f"{model} is older than Gemini 4 {MIN_TIER.capitalize()}. {advice}"
    return ""


# --------------------------------------------------------------------------- #
# Input and output.
# --------------------------------------------------------------------------- #
def read_file(path: Path, what: str) -> str:
    if not path.is_file():
        raise ReviewError(f"{what} file not found: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ReviewError(f"cannot read {what} file {path}: {exc}") from None


def read_source(args: argparse.Namespace) -> str:
    if args.text is not None and args.input is not None:
        raise ReviewError("pass --text or --input, not both.")
    if args.text is not None:
        text = args.text
    elif args.input is not None:
        text = read_file(args.input, "input")
    elif sys.stdin.isatty():
        raise ReviewError("nothing to review: pass --text, --input or pipe the text on stdin.")
    else:
        text = sys.stdin.read()
    if not text.strip():
        raise ReviewError("nothing to review: the input is empty.")
    if len(text) > MAX_CHARS:
        raise ReviewError(f"the text has {len(text)} characters, more than {MAX_CHARS} for one call: split "
                          "the document (by chapter or section) and review each part.")
    return text


def check_output(out: Path | None, source: Path | None) -> None:
    """Fail before spending anything if the output cannot be written or would replace the source."""
    if out is None:
        return
    if source is not None and out.resolve() == source.resolve():
        raise ReviewError("--output is the input file: the skill never overwrites the source. "
                          "Choose another path.")
    if out.is_dir():
        raise ReviewError(f"--output is a directory, give a file path: {out}")
    parent = out.parent.resolve()
    while not parent.exists():
        parent = parent.parent
    if not parent.is_dir() or not os.access(parent, os.W_OK):
        raise ReviewError(f"cannot write under {parent}.")


def write_text(text: str, out: Path | None) -> None:
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


def deliver(source: str, result: dict, out: Path | None) -> None:
    """Write the revision, or keep it aside with exit 4 when protected content changed."""
    revised = result["revised"]
    problems = check_invariants(source, revised)
    if not problems:
        write_text(revised, out)
        return
    if out:
        kept = out.with_name(out.name + ".unchecked")
        kept.parent.mkdir(parents=True, exist_ok=True)
        kept.write_text(revised, encoding="utf-8")
        where = f"the revision is in {kept}"
    else:
        sys.stdout.write(revised if revised.endswith("\n") else revised + "\n")
        where = "the revision was printed above"
    details = "\n  - ".join(problems)
    raise ReviewError(f"the revision changed protected content ({where}):\n  - {details}", 4)


# --------------------------------------------------------------------------- #
# Settings resolution.
# --------------------------------------------------------------------------- #
def resolve(args: argparse.Namespace, cwd: Path) -> dict:
    """Backend, model, thinking and timeout after files, environment and flags."""
    settings = {key: value for key, (value, _) in er_config.effective(cwd).items()}
    backend = args.via or settings["backend"]
    if backend == "auto":
        backend = "agy" if er_agy.available() else "api"
    model = args.model or os.environ.get(MODEL_ENV, "").strip() or settings[f"{backend}_model"]
    return {"backend": backend, "model": model,
            "thinking": args.thinking or settings["api_thinking"],
            "timeout": args.timeout or settings["timeout"]}


def run_backend(run: dict, instruction: str, text: str) -> dict:
    if run["backend"] == "agy":
        return er_agy.review(instruction, text, model=run["model"], timeout=run["timeout"])
    return er_api.review(instruction, text, model=run["model"], thinking=run["thinking"], timeout=run["timeout"])


def describe_backend(run: dict, instruction: str, text: str) -> str:
    if run["backend"] == "agy":
        return er_agy.describe(instruction, text, model=run["model"], timeout=run["timeout"])
    return er_api.describe(instruction, text, model=run["model"], thinking=run["thinking"])


# --------------------------------------------------------------------------- #
# Command line.
# --------------------------------------------------------------------------- #
class Parser(argparse.ArgumentParser):
    """Usage errors exit 1, so exit 2 keeps meaning "backend unavailable"."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        raise ReviewError(message)


def positive(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def review_parser() -> Parser:
    ap = Parser(prog="gemini_editorial_review.py",
                description="Editorial review of a text, in its own language, by Gemini. "
                            "Run `gemini_editorial_review.py config` for the settings.")
    ap.add_argument("-t", "--text", help="Text to review.")
    ap.add_argument("-i", "--input", type=Path, help="File to review (default: stdin).")
    ap.add_argument("-o", "--output", type=Path, help="Where to write the revision (default: stdout).")
    ap.add_argument("--via", choices=er_config.BACKENDS, help="Backend for this run (default: the setting).")
    ap.add_argument("--profile", choices=PROFILES + ("auto",), default="auto",
                    help="Kind of text (default: inferred).")
    ap.add_argument("--audience", default="", help="Who reads the text, in a few words.")
    ap.add_argument("--rules", type=Path, action="append", default=[],
                    help="House rules file (style guide, writing rules); repeatable, later files win.")
    ap.add_argument("--glossary", type=Path, help="Terminology file whose terms must be kept.")
    ap.add_argument("--lang", help="Language code whose notes to send (default: detected).")
    ap.add_argument("--model", help=f"Model id (default: ${MODEL_ENV} or the backend's setting).")
    ap.add_argument("--thinking", choices=er_config.THINKING, help="Thinking level, api backend only.")
    ap.add_argument("--timeout", type=positive, help="Seconds allowed for the review.")
    ap.add_argument("--print-prompt", action="store_true",
                    help="Print what would be sent (no key, no agy run) and exit.")
    return ap


def config_parser() -> Parser:
    ap = Parser(prog="gemini_editorial_review.py config", description="Show or change the settings.")
    sub = ap.add_subparsers(dest="action")
    sub.add_parser("show", help="Each setting, its value and where it comes from (the default action).")
    for action in ("set", "unset"):
        cmd = sub.add_parser(action, help=f"{action.capitalize()} a setting in the user file (default) "
                                          "or the project file.")
        cmd.add_argument("key", choices=list(er_config.KEYS))
        if action == "set":
            cmd.add_argument("value")
        cmd.add_argument("--project", action="store_true", help="Write the project file instead.")
    return ap


def run_config(argv: list[str]) -> None:
    args = config_parser().parse_args(argv)
    cwd = Path.cwd()
    if args.action in (None, "show"):
        print(er_config.render(cwd))
        return
    scope = "project" if args.project else "user"
    if args.action == "set":
        path = er_config.set_value(scope, args.key, args.value, cwd)
        print(f"{args.key} = {er_config.read_file(path)[args.key]} in {path}")
    else:
        path = er_config.unset_value(scope, args.key, cwd)
        print(f"{args.key} removed from {path}")


def run_review(argv: list[str]) -> None:
    args = review_parser().parse_args(argv)
    rules = [(path.name, read_file(path, "rules")) for path in args.rules]
    glossary = read_file(args.glossary, "glossary") if args.glossary else ""
    source = read_source(args)
    run = resolve(args, Path.cwd())
    warning = model_warning(run["model"])
    if warning:
        print(f"WARNING: {warning}", file=sys.stderr)
    lang = args.lang.strip().lower().split("-")[0] if args.lang else detect_language(source)
    instruction = system_instruction(args.profile, lang=lang, audience=args.audience,
                                     rules=rules, glossary=glossary)
    if args.print_prompt:
        print(f"# backend: {run['backend']} · model: {run['model']}")
        print(describe_backend(run, instruction, source))
        return
    check_output(args.output, args.input)
    print(f"backend: {run['backend']} · model: {run['model']}", file=sys.stderr)
    result = run_backend(run, instruction, source)
    report(result, args.profile == "auto")
    deliver(source, result, args.output)


def on_signal(signum: int, frame: object) -> None:
    raise SystemExit(128 + signum)  # unwinds through er_agy, which then kills agy's process group


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    try:
        if argv[:1] == ["config"]:
            run_config(argv[1:])
        else:
            run_review(argv)
    except ReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(exc.code)


if __name__ == "__main__":
    for _signum in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(_signum, on_signal)
    main()
