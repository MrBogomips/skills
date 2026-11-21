"""Backend `agy`: one print-mode turn of the local Antigravity CLI, on the user's agy login and quota.

agy has no system-prompt option, so the instruction and the text travel in one prompt, the text
between markers. The turn runs in an empty temporary workspace with no tools: MCP servers, file
writes and terminal commands are denied, whatever the user's own agy settings are.

A turn that has not started within START_TIMEOUT_SECONDS (most often an MCP server configured in
agy that never connects) is killed with its process group, and the agy log is read for the cause.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from er_text import RESPONSE_SCHEMA, ReviewError, parse_answer

START_TIMEOUT_SECONDS = 90
BACKSTOP_SECONDS = 60
POLL_SECONDS = 2
AGY_SETTINGS = {
    "toolPermission": "always-proceed",          # print mode cannot ask; every tool below is denied
    "permissions": {"deny": ["mcp(*)", "write_file(*)", "command(*)"]},
}
TEXT_START = "=== TEXT TO REVISE ==="
TEXT_END = "=== END OF TEXT ==="
STALL_RE = re.compile(r"MCP: \d+ server\(s\) still connecting after \S+: (.+)")


class TurnNotStarted(Exception):
    """agy did not start the turn within START_TIMEOUT_SECONDS and was killed."""


def available() -> bool:
    return shutil.which("agy") is not None


def build_prompt(instruction: str, text: str) -> str:
    return (f"{instruction}\n\n## Text\n\nThe text to revise is between the markers {TEXT_START} and "
            f"{TEXT_END}; the markers are not part of it. Use no tools: everything you need is here.\n\n"
            f"{TEXT_START}\n{text}\n{TEXT_END}")


def command(prompt: str, model: str, trace_path: Path, timeout: int) -> list[str]:
    return ["agy", "-p", prompt, "--model", model, "--output-format", "stream-json",
            "--print-timeout", f"{timeout}s", "--log-file", str(trace_path.with_suffix(".log")),
            "--disable-slash-commands", "--settings", json.dumps(AGY_SETTINGS),
            "--json-schema", json.dumps(RESPONSE_SCHEMA)]


def events(trace_path: Path) -> list[dict]:
    if not trace_path.is_file():
        return []
    found = []
    for line in trace_path.read_text(errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            found.append(event)
    return found


def turn_started(trace_path: Path) -> bool:
    """True once agy's trace shows a step: the turn has started."""
    return any("step_update" in event for event in events(trace_path))


def final_result(trace_path: Path) -> tuple[str | None, str | None]:
    """(response, error) from the trace's `result` event."""
    response, error = None, None
    for event in events(trace_path):
        if event.get("event") != "result":
            continue
        result = event.get("result") or {}
        response = result.get("response")
        if result.get("status") != "SUCCESS":
            error = f"agy result status {result.get('status')}"
            if result.get("error"):
                error += f": {result['error']}"
    return response, error


def diagnose(trace_path: Path) -> str:
    """A hint from agy's log about why the turn stalled, or an empty string."""
    log_path = trace_path.with_suffix(".log")
    if not log_path.is_file():
        return ""
    stalled = STALL_RE.findall(log_path.read_text(errors="replace"))
    if not stalled:
        return ""
    return (f" agy was still waiting for MCP server(s) to connect: {stalled[-1].strip()}."
            " A print-mode turn does not start until they do: repair them or run `agy mcp remove <name>`"
            " (`agy mcp disable` is not enough).")


def kill(proc: subprocess.Popen) -> None:
    """Kill agy and every process in its group (its MCP servers included)."""
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        proc.kill()
    proc.wait()


def watch(proc: subprocess.Popen, trace_path: Path, timeout: int, started_at: float) -> int:
    """Wait for agy to exit, killing it if the turn never starts or outlives its timeout."""
    started = False
    while True:
        try:
            return proc.wait(timeout=POLL_SECONDS)
        except subprocess.TimeoutExpired:
            pass
        elapsed = time.monotonic() - started_at
        started = started or turn_started(trace_path)
        if not started and elapsed > START_TIMEOUT_SECONDS:
            raise TurnNotStarted()
        if elapsed > timeout + BACKSTOP_SECONDS:
            raise subprocess.TimeoutExpired("agy", timeout + BACKSTOP_SECONDS)


def call_agy(prompt: str, model: str, run_dir: Path, timeout: int) -> Path:
    """Run one turn in run_dir/workspace, streaming to run_dir/turn.jsonl. Return the trace path."""
    workspace = run_dir / "workspace"
    workspace.mkdir(exist_ok=True)
    trace_path = run_dir / "turn.jsonl"
    started_at = time.monotonic()
    with trace_path.open("w") as trace:
        proc = subprocess.Popen(command(prompt, model, trace_path, timeout), cwd=workspace,
                                stdin=subprocess.DEVNULL, stdout=trace, stderr=subprocess.STDOUT, text=True,
                                start_new_session=True)
        try:
            watch(proc, trace_path, timeout, started_at)
        except BaseException:  # watchdog, backstop, signal or a watcher failure: never leave agy running
            kill(proc)
            raise
    return trace_path


def run_turn(prompt: str, model: str, run_dir: Path, timeout: int) -> str:
    """The model's raw answer, or a ReviewError (code 2 when agy could not start the turn)."""
    try:
        trace_path = call_agy(prompt, model, run_dir, timeout)
    except TurnNotStarted:
        raise ReviewError(f"agy did not start the turn within {START_TIMEOUT_SECONDS}s, so nothing was "
                          f"reviewed.{diagnose(run_dir / 'turn.jsonl')} This is a problem with agy's "
                          f"installation or configuration. Trace and log: {run_dir}", 2) from None
    except subprocess.TimeoutExpired:
        raise ReviewError(f"agy did not finish within {timeout}s. Trace and log: {run_dir}") from None
    response, error = final_result(trace_path)
    if error or not response:
        started = turn_started(trace_path)
        reason = error or "agy ended without a result"
        hint = "" if started else diagnose(trace_path)
        raise ReviewError(f"{reason}.{hint} Trace and log: {run_dir}", 1 if started else 2)
    return response


def review(instruction: str, text: str, *, model: str, timeout: int) -> dict:
    if not available():
        raise ReviewError("agy not found on PATH: install the Antigravity CLI and log in, "
                          "or use the api backend.", 2)
    run_dir = Path(tempfile.mkdtemp(prefix="gemini-editorial-"))
    result = parse_answer(run_turn(build_prompt(instruction, text), model, run_dir, timeout))
    shutil.rmtree(run_dir, ignore_errors=True)  # kept on failure, for the trace and the log
    return result


def describe(instruction: str, text: str, *, model: str, timeout: int) -> str:
    """The agy command line that would run, with the prompt shown in full after it."""
    prompt = build_prompt(instruction, text)
    cmd = command("<prompt below>", model, Path("<run-dir>/turn.jsonl"), timeout)
    return " ".join(cmd[:1] + [json.dumps(part) if " " in part or "{" in part else part
                               for part in cmd[1:]]) + "\n\n" + prompt
