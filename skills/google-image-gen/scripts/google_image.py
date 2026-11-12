#!/usr/bin/env python3
"""Generate or edit images with the Gemini API (Nano Banana models).

Needs an API key in GEMINI_API_KEY (or GOOGLE_API_KEY). The key is sent in the
x-goog-api-key header only. Every call is billed to that key.

    google_image.py -p "a red bicycle in the rain" -o bike.png
    google_image.py --edit v1.png -p "make the sky purple" -o v2.png
    google_image.py -p "..." -o cover.png --aspect 9:16 --fit 1080x1920

Standard library only; --fit additionally needs Pillow.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import socket
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
API_REVISION = "2026-05-20"          # sent as Api-Revision, as in the Gemini API docs
DEFAULT_MODEL = "gemini-nano-banana-2.1"
KEY_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY")
KEY_SHAPE_RE = re.compile(r"AIza[0-9A-Za-z_-]{20,}")

EDIT_NOTE = ("The attached image is the edit target. Produce an updated version of it that "
             "applies only the change described below and keeps everything else identical.")
REFERENCE_NOTE = "Use the attached image(s) as visual reference for the request below."

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


def image_part(path: Path) -> dict:
    raw = path.read_bytes()
    kind = sniff(raw)
    if kind is None:
        die(f"{path} is not a PNG, JPEG or WebP image.")
    mime = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}[kind]
    return {"type": "image", "mime_type": mime, "data": base64.b64encode(raw).decode("ascii")}


def build_request(model: str, request: str, images: list[Path], *,
                  edit: bool, aspect: str | None) -> dict:
    text = request
    if edit:
        text = f"{EDIT_NOTE}\n\n{request}"
    elif images:
        text = f"{REFERENCE_NOTE}\n\n{request}"
    body: dict = {"model": model,
                  "input": [{"type": "text", "text": text}] + [image_part(p) for p in images]}
    if aspect:
        body["response_format"] = {"type": "image", "aspect_ratio": aspect}
    return body


def preview(body: dict) -> str:
    """The request as it would be sent, minus image bytes and (always) the key."""
    shown = json.loads(json.dumps(body))
    for part in shown["input"]:
        if part.get("type") == "image":
            part["data"] = f"<{len(part['data'])} base64 chars omitted>"
    header = f"POST {ENDPOINT}\nApi-Revision: {API_REVISION}\nx-goog-api-key: <not shown>\n"
    return header + json.dumps(shown, indent=2)


def http_failure(code: int, detail: str) -> str:
    detail = f": {detail}" if detail else ""
    if code in (401, 403):
        return (f"the API key was rejected or lacks access (HTTP {code}){detail}. Check "
                "GEMINI_API_KEY and that it may use image models (they need a billed project).")
    if code == 400:
        return f"the request was rejected (HTTP 400){detail}"
    if code == 429:
        return f"rate limit or quota exceeded (HTTP 429){detail}. Wait and retry later."
    if code >= 500:
        return f"the Gemini service failed (HTTP {code}){detail}"
    return f"unexpected HTTP {code}{detail}"


def error_detail(exc: urllib.error.HTTPError, key: str) -> str:
    try:
        message = json.loads(exc.read().decode("utf-8", "replace"))["error"]["message"]
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


def read_response(data: dict) -> tuple[list[tuple[bytes, str | None]], list[str]]:
    """(image bytes, MIME type) pairs and any text the model returned."""
    images: list[tuple[bytes, str | None]] = []
    texts: list[str] = []
    for step in data.get("steps") or []:
        if step.get("type") != "model_output":
            continue
        for block in step.get("content") or []:
            if block.get("type") == "image" and block.get("data"):
                try:
                    images.append((base64.b64decode(block["data"]), block.get("mime_type")))
                except ValueError:
                    die("the API returned image data that is not valid base64.")
            elif block.get("type") == "text" and block.get("text"):
                texts.append(block["text"])
    return images, texts


def no_image_reason(data: dict, texts: list[str]) -> str:
    if texts:
        return "the model replied with text only: " + " ".join(texts)[:400]
    status = data.get("status")
    hint = f" (status: {status})" if status else ""
    return f"the response held no image{hint}; the prompt may have been blocked by a safety filter."


def generate_one(body: dict, key: str, timeout: int) -> tuple[bytes, str]:
    data = call_api(body, key, timeout)
    images, texts = read_response(data)
    if not images:
        die(f"{scrub(no_image_reason(data, texts), key)} Nothing was written.")
    raw, mime = images[-1]
    kind = sniff(raw, mime)
    if kind is None:
        die("the API returned data that is not PNG, JPEG or WebP; nothing was written.")
    return raw, kind


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Generate or edit an image with the Gemini API (billed to your API key).")
    ap.add_argument("-p", "--prompt", help="What to generate, or the change to make with --edit.")
    ap.add_argument("--prompt-file", type=Path, help="Read the prompt from a file instead.")
    ap.add_argument("-o", "--output", type=Path, required=True, help="Where to write the image.")
    ap.add_argument("--edit", type=Path, help="Image to change; everything else is kept.")
    ap.add_argument("-r", "--reference", type=Path, action="append", default=[],
                    help="Reference image to attach (repeatable).")
    ap.add_argument("--aspect", help="Aspect ratio sent to the API, e.g. 16:9, 9:16, 1:1.")
    ap.add_argument("-n", "--variants", type=int, default=1,
                    help="Number of images; each is a separate billed call, extras saved as <name>-2.png etc.")
    ap.add_argument("--fit", metavar="WxH", help="Force the saved file to exactly WxH (needs Pillow).")
    ap.add_argument("--fit-mode", choices=("pad", "crop"), default="pad",
                    help="--fit reconciles the aspect by padding (default) or center-cropping.")
    ap.add_argument("--model", default=os.environ.get("GOOGLE_IMAGE_MODEL") or DEFAULT_MODEL,
                    help=f"Model id (default: $GOOGLE_IMAGE_MODEL or {DEFAULT_MODEL}).")
    ap.add_argument("--timeout", type=int, default=300, help="Seconds per API call (default: 300).")
    ap.add_argument("--print-prompt", action="store_true",
                    help="Print the request that would be sent (no key) and exit without calling the API.")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    request = read_request(args.prompt, args.prompt_file)
    images = check_images(args.edit, args.reference)
    if not 1 <= args.variants <= 8:
        die("--variants must be between 1 and 8.")
    if args.aspect:
        parse_aspect(args.aspect)
    size = parse_size(args.fit) if args.fit else None
    body = build_request(args.model, request, images, edit=bool(args.edit), aspect=args.aspect)
    if args.print_prompt:
        print(preview(body))
        return
    if size:
        require_pillow()
    check_output_dir(args.output)
    key = api_key()

    payloads, kinds = [], []
    for _ in range(args.variants):
        raw, kind = generate_one(body, key, args.timeout)
        payloads.append(raw)
        kinds.append(kind)
    if size:
        payloads = [fit_to_size(raw, size, args.fit_mode) for raw in payloads]
        kinds = ["png"] * len(payloads)
    write_images(output_paths(args.output, kinds), payloads)


if __name__ == "__main__":
    main()
