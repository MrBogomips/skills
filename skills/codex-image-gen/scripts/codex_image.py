#!/usr/bin/env python3
"""Generate or edit images with the codex CLI's built-in image tool.

`codex exec` has no "write the image to this path" flag: it saves what it
generates under `$CODEX_HOME/generated_images/<session id>/`. This script runs
one non-interactive turn, collects only that session's images, and writes them
where you asked, with extensions matching their real format.

    codex_image.py -p "a red bicycle in the rain" -o bike.png
    codex_image.py --edit v1.png -p "make the sky purple" -o v2.png
    codex_image.py -p "..." -o cover.png --aspect 9:16 --fit 1080x1920

Standard library only; --fit additionally needs Pillow.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# The model must be told, forcefully, to call its image tool; otherwise it
# describes the image or draws one with ImageMagick and the run yields nothing.
PREAMBLE = """You MUST actually generate a real image this turn with your built-in image generation tool (the `imagegen` skill / `image_gen` tool). Do not merely describe it or claim it is done - the run fails unless the tool genuinely runs and emits an image.

Do NOT draw, composite, or edit the picture yourself with ImageMagick, Python, PIL, canvas, or SVG, and do NOT use the API-key CLI fallback. Do NOT save, copy, move, or rename the result yourself: it is collected automatically from where the tool puts it. Reply with one short line of confirmation and nothing else.

If the built-in image generation tool is unavailable, say so explicitly and do nothing else."""

EDIT_NOTE = """The attached image is the edit target. Produce an UPDATED VERSION of it that applies the requested change while keeping everything else looking identical. This is an edit of the attached image, NOT a new image from scratch. Apply only the change described below."""
REFERENCE_NOTE = "Use the attached image(s) as visual reference for the request below."
ASPECT_NOTE = "Generate the image at a {aspect} aspect ratio, at the largest size available for that shape."
VARIANTS_NOTE = """Produce {count} distinct variants of this image in this same turn, each from its own image-tool call. Vary the interpretation between them; do not return near-duplicates."""

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")
SESSION_ID_RE = re.compile(r"session id:\s*([0-9a-fA-F-]{36})")
TAIL_LINES = 12

# --------------------------------------------------------------------------- #
# Shared helpers. Kept textually identical in codex_image.py and google_image.py
# (each skill is installed on its own); tests/test_image_gen.py enforces that.
# --------------------------------------------------------------------------- #
MIME_KINDS = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
ASPECT_RE = re.compile(r"^([1-9][0-9]?):([1-9][0-9]?)$")
SIZE_RE = re.compile(r"^([1-9][0-9]*)[xX]([1-9][0-9]*)$")


def die(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


def sniff(raw: bytes, mime: str | None = None) -> str | None:
    """Image kind (png, jpg, webp) from the bytes, else from the MIME type."""
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "webp"
    return MIME_KINDS.get((mime or "").lower())


def parse_aspect(value: str) -> str:
    if not ASPECT_RE.match(value):
        die(f"--aspect expects W:H such as 16:9, got {value!r}.")
    return value


def parse_size(spec: str) -> tuple[int, int]:
    match = SIZE_RE.match(spec)
    if not match:
        die(f"--fit expects WxH such as 1080x1920, got {spec!r}.")
    return int(match.group(1)), int(match.group(2))


def require_pillow() -> None:
    try:
        import PIL  # noqa: F401
    except ImportError:
        die("--fit needs Pillow (pip install Pillow); nothing was generated.")


def fit_to_size(raw: bytes, size: tuple[int, int], mode: str) -> bytes:
    """Pad (black bars) or center-crop to the target aspect, then resize to exactly size."""
    from io import BytesIO

    from PIL import Image

    want_w, want_h = size
    with Image.open(BytesIO(raw)) as src:
        img = src.convert("RGB")
    w, h = img.size
    target, current = want_w / want_h, w / h
    if abs(current - target) < 1e-3:
        staged = img
    elif mode == "crop":
        if current > target:                       # too wide: trim the sides
            new_w = round(h * target)
            left = (w - new_w) // 2
            staged = img.crop((left, 0, left + new_w, h))
        else:                                      # too tall: trim top and bottom
            new_h = round(w / target)
            top = (h - new_h) // 2
            staged = img.crop((0, top, w, top + new_h))
    elif current > target:                         # pad: too wide, bars above and below
        new_h = round(w / target)
        staged = Image.new("RGB", (w, new_h), "black")
        staged.paste(img, (0, (new_h - h) // 2))
    else:                                          # pad: too tall, bars left and right
        new_w = round(h * target)
        staged = Image.new("RGB", (new_w, h), "black")
        staged.paste(img, ((new_w - w) // 2, 0))
    out = BytesIO()
    staged.resize((want_w, want_h), Image.LANCZOS).save(out, format="PNG")
    return out.getvalue()


def output_paths(out: Path, kinds: list[str]) -> list[Path]:
    """One path per image: extension follows the format, extras become <stem>-2, <stem>-3."""
    paths = []
    for index, kind in enumerate(kinds, start=1):
        ext = out.suffix.lower()
        same = ext == f".{kind}" or (kind == "jpg" and ext == ".jpeg")
        path = out if same else out.with_suffix(f".{kind}")
        if index > 1:
            path = path.with_name(f"{path.stem}-{index}{path.suffix}")
        paths.append(path)
    return paths


def check_output_dir(out: Path) -> None:
    """Fail before spending anything if the output cannot be written."""
    if out.is_dir():
        die(f"--output is a directory, give a file path: {out}")
    parent = out.parent.resolve()
    while not parent.exists():
        parent = parent.parent
    if not parent.is_dir() or not os.access(parent, os.W_OK):
        die(f"cannot write under {parent}.")


def read_request(prompt: str | None, prompt_file: Path | None) -> str:
    if prompt and prompt_file:
        die("pass --prompt or --prompt-file, not both.")
    if prompt_file:
        if not prompt_file.is_file():
            die(f"prompt file not found: {prompt_file}")
        prompt = prompt_file.read_text(encoding="utf-8")
    if not prompt or not prompt.strip():
        die("a non-empty --prompt or --prompt-file is required.")
    return prompt.strip()


def check_images(edit: Path | None, refs: list[Path]) -> list[Path]:
    """Edit target first, then references; every file must exist."""
    images = ([edit] if edit else []) + list(refs)
    for image in images:
        if not image.is_file():
            die(f"image not found: {image}")
    return images


def write_images(paths: list[Path], payloads: list[bytes]) -> None:
    for path, raw in zip(paths, payloads):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        print(f"Wrote {path} ({len(raw):,} bytes)")
# --------------------------------------------------------------------------- #


def codex_bin() -> str:
    return os.environ.get("CODEX_BIN", "codex")


def generated_images_dir() -> Path:
    home = os.environ.get("CODEX_HOME")
    return (Path(home) if home else Path.home() / ".codex") / "generated_images"


def build_prompt(request: str, *, edit: bool, has_refs: bool,
                 aspect: str | None, variants: int = 1) -> str:
    parts = [PREAMBLE, ""]
    if edit:
        parts += [EDIT_NOTE, ""]
    elif has_refs:
        parts += [REFERENCE_NOTE, ""]
    if aspect:
        parts += [ASPECT_NOTE.format(aspect=aspect), ""]
    if variants > 1:
        parts += [VARIANTS_NOTE.format(count=variants), ""]
    parts += ["## Change to make" if edit else "## Image to generate", request.strip()]
    return "\n".join(parts).strip() + "\n"


def tail_of(transcript: str) -> str:
    return "\n".join(transcript.strip().splitlines()[-TAIL_LINES:])


def check_codex(binary: str) -> None:
    """The binary exists and is logged in, checked before any quota is spent."""
    if shutil.which(binary) is None:
        die(f"codex CLI not found on PATH as '{binary}'. Install it and run `codex login`, "
            "or set CODEX_BIN.")
    try:
        status = subprocess.run([binary, "login", "status"], capture_output=True,
                                text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        die(f"could not run `{binary} login status`: {exc}")
    if status.returncode != 0:
        die("codex is not logged in. Run `codex login`, then retry.")


def run_codex(prompt: str, images: list[Path], timeout: int) -> tuple[float, str, str]:
    """Run one `codex exec` turn. Returns (start time, session id, transcript)."""
    binary = codex_bin()
    cmd = [binary, "exec", "--skip-git-repo-check", "-s", "read-only",
           "-c", "model_reasoning_effort=high", prompt]        # prompt before the variadic -i
    for image in images:
        cmd += ["-i", str(image)]
    start = time.time()
    print("codex: generating (usually 30-60 s)...", file=sys.stderr)
    proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    try:
        # codex prints its banner, session id included, on stderr: merged above.
        transcript, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        die(f"codex exec timed out after {timeout}s; nothing was written.")
    if proc.returncode != 0:
        lowered = transcript.lower()
        if "usage limit" in lowered:
            die("the codex account is out of quota; no image was generated. "
                "Wait for the reset codex reports, or use another account.")
        if "not logged in" in lowered or "unauthorized" in lowered:
            die("codex rejected the login. Run `codex login`, then retry.")
        die(f"codex exec failed (exit {proc.returncode}):\n{tail_of(transcript)}")
    match = SESSION_ID_RE.search(transcript)
    session_id = match.group(1) if match else None
    if session_id is None:
        die("codex did not report a session id, so this run's images cannot be "
            f"identified; nothing was written.\n{tail_of(transcript)}")
    return start, session_id, transcript


def collect_images(session_id: str, start: float) -> list[bytes]:
    """Images codex saved for exactly this session, oldest first."""
    folder = generated_images_dir() / session_id
    if not folder.is_dir():
        return []
    files = [p for p in folder.iterdir()
             if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
             and p.stat().st_mtime >= start - 1]
    files.sort(key=lambda p: p.stat().st_mtime)
    return [p.read_bytes() for p in files]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Generate or edit an image with the codex CLI's built-in image tool.")
    ap.add_argument("-p", "--prompt", help="What to generate, or the change to make with --edit.")
    ap.add_argument("--prompt-file", type=Path, help="Read the prompt from a file instead.")
    ap.add_argument("-o", "--output", type=Path, required=True, help="Where to write the image.")
    ap.add_argument("--edit", type=Path, help="Image to change; everything else is kept.")
    ap.add_argument("-r", "--reference", type=Path, action="append", default=[],
                    help="Reference image to attach (repeatable).")
    ap.add_argument("--aspect", help="Aspect-ratio hint for the model, e.g. 16:9, 9:16, 1:1.")
    ap.add_argument("-n", "--variants", type=int, default=1,
                    help="Ask for N variants in one run; extras are saved as <name>-2.png etc.")
    ap.add_argument("--fit", metavar="WxH", help="Force the saved file to exactly WxH (needs Pillow).")
    ap.add_argument("--fit-mode", choices=("pad", "crop"), default="pad",
                    help="--fit reconciles the aspect by padding (default) or center-cropping.")
    ap.add_argument("--timeout", type=int, default=900, help="Seconds to wait (default: 900).")
    ap.add_argument("--print-prompt", action="store_true",
                    help="Print the assembled prompt and exit without running codex.")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    request = read_request(args.prompt, args.prompt_file)
    images = check_images(args.edit, args.reference)
    if args.variants < 1:
        die("--variants must be at least 1.")
    if args.aspect:
        parse_aspect(args.aspect)
    size = parse_size(args.fit) if args.fit else None
    prompt = build_prompt(request, edit=bool(args.edit), has_refs=bool(args.reference),
                          aspect=args.aspect, variants=args.variants)
    if args.print_prompt:
        print(prompt)
        return
    if size:
        require_pillow()
    check_output_dir(args.output)
    check_codex(codex_bin())

    start, session_id, transcript = run_codex(prompt, images, args.timeout)
    payloads = collect_images(session_id, start)
    if not payloads:
        die(f"codex produced no image in {generated_images_dir() / session_id}; nothing was "
            f"written. It probably answered in text instead of calling its image tool. "
            f"Re-run with a clearer picture request.\ncodex said:\n{tail_of(transcript)}")
    kinds = []
    for raw in payloads:
        kind = sniff(raw)
        if kind is None:
            die(f"codex saved {len(raw)} bytes that are not PNG, JPEG or WebP; nothing was written.")
        kinds.append(kind)
    if size:
        payloads = [fit_to_size(raw, size, args.fit_mode) for raw in payloads]
        kinds = ["png"] * len(payloads)
    write_images(output_paths(args.output, kinds), payloads)


if __name__ == "__main__":
    main()
