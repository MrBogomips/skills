"""Backend `api`: the Gemini Interactions API, with an API key. Every call is billed to that key.

The key is read from GEMINI_API_KEY (or GOOGLE_API_KEY) and sent in the x-goog-api-key header only.
"""
from __future__ import annotations

import json
import os
import re
import socket
import ssl
import urllib.error
import urllib.request

from er_text import RESPONSE_SCHEMA, ReviewError, parse_answer

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
API_REVISION = "2026-05-20"          # sent as Api-Revision, as in the Gemini API docs
KEY_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY")
KEY_SHAPE_RE = re.compile(r"AIza[0-9A-Za-z_-]{20,}")


def api_key() -> str:
    for name in KEY_VARS:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    raise ReviewError("no API key: set GEMINI_API_KEY (or GOOGLE_API_KEY) to your Gemini API key, "
                      "or use the agy backend.", 2)


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


def build_request(model: str, thinking: str, instruction: str, text: str) -> dict:
    return {"model": model, "input": text, "system_instruction": instruction,
            "generation_config": {"thinking_level": thinking},
            "response_format": {"type": "text", "mime_type": "application/json",
                                "schema": RESPONSE_SCHEMA}}


def preview(body: dict) -> str:
    header = f"POST {ENDPOINT}\nApi-Revision: {API_REVISION}\nx-goog-api-key: <not shown>\n"
    return header + json.dumps(body, indent=2, ensure_ascii=False)


def post_once(body: dict, key: str, timeout: int) -> dict:
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": key,
                 "Api-Revision": API_REVISION})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_api(body: dict, key: str, timeout: int) -> dict:
    """POST once; retry a single time on a 5xx or a timeout."""
    for attempt in (1, 2):
        try:
            return post_once(body, key, timeout)
        except urllib.error.HTTPError as exc:
            if exc.code >= 500 and attempt == 1:
                continue
            raise ReviewError(http_failure(exc.code, error_detail(exc, key))) from None
        except (socket.timeout, TimeoutError):
            if attempt == 1:
                continue
            raise ReviewError(f"the Gemini API timed out twice ({timeout}s each); nothing was written.") from None
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (socket.timeout, TimeoutError)) and attempt == 1:
                continue
            raise ReviewError(f"could not reach the Gemini API: {scrub(str(exc.reason), key)}") from None
        except ValueError:
            raise ReviewError("the Gemini API returned a response that is not JSON.") from None
    return {}


def answer_text(data: dict) -> str:
    texts = [block["text"] for step in data.get("steps") or [] if step.get("type") == "model_output"
             for block in step.get("content") or [] if block.get("type") == "text" and block.get("text")]
    if not texts:
        status = data.get("status") or "unknown"
        raise ReviewError(f"the response held no text (status: {status}); the text may have been blocked "
                          "by a safety filter. Nothing was written.")
    return "".join(texts)


def review(instruction: str, text: str, *, model: str, thinking: str, timeout: int) -> dict:
    key = api_key()
    data = call_api(build_request(model, thinking, instruction, text), key, timeout)
    return parse_answer(answer_text(data))


def describe(instruction: str, text: str, *, model: str, thinking: str) -> str:
    """The request that would be sent, without the key."""
    return preview(build_request(model, thinking, instruction, text))

