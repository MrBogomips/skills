#!/usr/bin/env python3
"""Run one round of Gemini web research: one agy job per question, all in parallel.

Usage: gemini_research.py '<question 1>' '<question 2>' ...

Each job runs a Gemini model (default gemini-3.8-flash-high, override with the environment
variable GEMINI_RESEARCH_MODEL) in agy print mode. Set GEMINI_RESEARCH_SANDBOX=1 to add agy --sandbox. The worker must search,
read the pages it cites with read_page.py, and back every claim with a verbatim quote. The script reads
the job's trace and checks that:
  - the worker called search_web (a job with no search fails),
  - the worker read at least one page (a job that read none fails),
  - each claim's URL is a page the worker read,
  - each claim's quote appears in the text of the pages it read,
  - every URL in the answer was read.
Prints one checked report per question. Traces are kept in the run directory printed
at the top. Exits 1 if any job failed, 2 if agy is not installed.
"""

import concurrent.futures
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MODEL = os.environ.get("GEMINI_RESEARCH_MODEL") or "gemini-3.8-flash-high"
SANDBOX = os.environ.get("GEMINI_RESEARCH_SANDBOX") == "1"
JOB_TIMEOUT_SECONDS = 900
MAX_PAGES = 6
MAX_SEARCHES = 8
READER = Path(__file__).resolve().parent / "read_page.py"

SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "url": {"type": "string"},
                    "quote": {"type": "string"},
                },
                "required": ["claim", "url", "quote"],
            },
        },
        "unconfirmed": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["answer", "claims", "unconfirmed"],
}

PROMPT = """You are a web research worker. Answer the question below from live web sources.

Question: {question}

Rules:
1. Call search_web before writing anything, at least twice and at most {max_searches} times, with different queries, even if you think you already know the answer. Your memory is not a source.
2. Read pages only with this exact terminal command, one page per call: python3 {reader} '<url>'
   Run no other terminal commands, do not use read_url_content, and use no browser. Read at most {max_pages} pages, each once, chosen from your search results. For a file in a GitHub repository, read its raw.githubusercontent.com URL. Prefer primary sources: official docs, the project's own repository, release notes, the original announcement or paper. Use blogs, forums and aggregators only for what primary sources do not cover.
3. Every claim must come from a page you read in this session. Give the exact URL you read and a verbatim quote of 5 to 30 words from that page's output, copied character for character. Search result snippets are not quotable.
4. Never guess a URL, repository owner, version, date, price or number. Anything you could not confirm on a page you read goes in "unconfirmed".
5. When dates matter, say whether a date is the page's publication date or the date of the event.
6. Create, edit or delete no files.

Return JSON:
- "answer": a concise markdown answer of at most 250 words. Link only URLs you read.
- "claims": one entry per substantive fact in the answer: {{"claim", "url", "quote"}}.
- "unconfirmed": things the question asks about that you could not confirm.
"""

URL_RE = re.compile(r"https?://[^\s)\]>\"'`]+")
SAVED_OUTPUT_RE = re.compile(r"file://(\S+?output\.txt)")


def normalize_text(text):
    return " ".join(re.sub(r"[^0-9a-z]+", " ", text.lower()).split())


def normalize_url(url):
    url = url.split("#", 1)[0].rstrip(".,;:")
    url = re.sub(r"^http://", "https://", url)
    url = re.sub(r"^https://www\.", "https://", url)
    return url.rstrip("/")


def read_trace(trace_path):
    """Return (search count, opened URLs, fetched text, final response, error)."""
    searches = 0
    opened = set()
    fetched = []
    response = None
    error = None
    for line in trace_path.read_text(errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        step = event.get("step_update")
        if step and step.get("step_type") == "tool" and step.get("state") == "DONE":
            info = step.get("tool_info") or {}
            name = info.get("name") or step.get("tool_name")
            output = info.get("output") or ""
            if name == "search_web":
                searches += 1
            command = json.dumps(info.get("parameters") or {})
            if name == "run_command" and READER.name in command:
                for url in URL_RE.findall(command):
                    opened.add(normalize_url(url))
                fetched.append(output)
                for saved in SAVED_OUTPUT_RE.findall(output):
                    saved_path = Path(saved)
                    if saved_path.is_file():
                        fetched.append(saved_path.read_text(errors="replace"))
        if event.get("event") == "result":
            result = event["result"]
            if result.get("status") != "SUCCESS":
                error = f"agy result status {result.get('status')}"
            response = result.get("response")
    return searches, opened, normalize_text("\n".join(fetched)), response, error


def run_agy(question, trace_path, cwd):
    """Run one agy print-mode job, streaming its output to trace_path. Return the exit code."""
    cmd = [
        "agy", "-p", PROMPT.format(question=question, max_pages=MAX_PAGES, max_searches=MAX_SEARCHES, reader=READER),
        "--model", MODEL,
        "--output-format", "stream-json",
        "--json-schema", json.dumps(SCHEMA),
    ]
    if SANDBOX:
        cmd.append("--sandbox")
    with trace_path.open("w") as trace:
        proc = subprocess.run(
            cmd, cwd=cwd, stdin=subprocess.DEVNULL, stdout=trace, stderr=subprocess.STDOUT,
            text=True, timeout=JOB_TIMEOUT_SECONDS,
        )
    return proc.returncode


def parse_report(response):
    """Parse and shape-check the worker's final JSON. Raise ValueError if it is malformed."""
    try:
        report = json.loads(response)
    except (json.JSONDecodeError, TypeError):
        raise ValueError("final response is not the required JSON")
    if not isinstance(report, dict):
        raise ValueError("final response is not a JSON object")
    if not isinstance(report.get("answer"), str):
        raise ValueError('report field "answer" is missing or not a string')
    unconfirmed = report.get("unconfirmed")
    if not isinstance(unconfirmed, list) or not all(isinstance(i, str) for i in unconfirmed):
        raise ValueError('report field "unconfirmed" is missing or not a list of strings')
    claims = report.get("claims")
    if not isinstance(claims, list):
        raise ValueError('report field "claims" is missing or not a list')
    for number, claim in enumerate(claims, 1):
        ok = isinstance(claim, dict) and all(isinstance(claim.get(k), str) for k in ("claim", "url", "quote"))
        if not ok:
            raise ValueError(f"claim {number} lacks string fields claim, url, quote")
    return report


def check_claim(claim, opened, fetched):
    """Return the list of problems with one claim (empty means OK)."""
    problems = []
    if normalize_url(claim["url"]) not in opened:
        problems.append("URL was never read")
    quote = normalize_text(claim["quote"])
    if len(quote.split()) < 5:
        problems.append("quote is under 5 words")
    elif quote not in fetched:
        problems.append("quote not found in pages read")
    return problems


def render_report(report, opened, fetched):
    """Return (markdown lines, flagged count) for a well-formed report."""
    lines = [report["answer"].strip(), "", "### Claims", ""]
    flagged = 0
    for number, claim in enumerate(report["claims"], 1):
        problems = check_claim(claim, opened, fetched)
        mark = "OK" if not problems else "FLAG (" + "; ".join(problems) + ")"
        flagged += bool(problems)
        lines += [f"{number}. [{mark}] {claim['claim']}", f"   {claim['url']}", f"   > {claim['quote']}"]
    if not report["claims"]:
        lines.append("FLAG: the worker returned no sourced claims.")
        flagged += 1

    unopened = sorted({u for u in URL_RE.findall(report["answer"]) if normalize_url(u) not in opened})
    if unopened:
        lines += ["", "### URLs in the answer that were never read (FLAG)", ""]
        lines += [f"- {u}" for u in unopened]
        flagged += len(unopened)

    if report["unconfirmed"]:
        lines += ["", "### Unconfirmed", ""]
        lines += [f"- {item}" for item in report["unconfirmed"]]
    lines += ["", f"Checks: {len(report['claims'])} claims, {flagged} flagged.", ""]
    return lines, flagged


def trace_failure(returncode, error, searches, opened, response):
    """Return why a job's trace disqualifies it, or None."""
    if returncode != 0:
        return f"agy exited {returncode}"
    if error:
        return error
    if searches == 0:
        return "the worker ran no web search, so its answer came from memory"
    if not opened:
        return "the worker read no pages, so its answer came from search snippets or memory"
    if response is None:
        return "no final response in the trace"
    return None


def run_job(index, question, run_dir):
    """Run and check one job. Never raises: any problem becomes a FAILED report."""
    trace_path = run_dir / f"job-{index}.jsonl"
    started = time.monotonic()
    lines = [f"## Job {index}: {question}", ""]
    try:
        returncode = run_agy(question, trace_path, run_dir)
        seconds = round(time.monotonic() - started)
        searches, opened, fetched, response, error = read_trace(trace_path)
        header = f"{searches} searches · {len(opened)} pages read · {seconds}s · trace {trace_path}"
        failure = trace_failure(returncode, error, searches, opened, response)
        if failure is None:
            report = parse_report(response)
    except subprocess.TimeoutExpired:
        failure, header = f"agy did not finish within {JOB_TIMEOUT_SECONDS}s", f"trace {trace_path}"
    except ValueError as exc:
        failure = str(exc)
    except Exception as exc:  # one bad job must not abort the round
        failure, header = f"unexpected {type(exc).__name__}: {exc}", f"trace {trace_path}"
    if failure:
        return False, "\n".join(lines + [f"FAILED: {failure}. {header}", ""])
    body, _ = render_report(report, opened, fetched)
    return True, "\n".join(lines + [header, ""] + body)


def main():
    questions = sys.argv[1:]
    if not questions:
        sys.exit("usage: gemini_research.py '<question 1>' '<question 2>' ...")
    if shutil.which("agy") is None:
        print("gemini_research: agy not found on PATH; install the Antigravity CLI and log in.", file=sys.stderr)
        sys.exit(2)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = Path(tempfile.mkdtemp(prefix=f"gemini-research-{stamp}-"))
    print(f"# Gemini research round: {len(questions)} jobs, {MODEL}\nRun directory: {run_dir}\n", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(questions)) as pool:
        jobs = [pool.submit(run_job, i, q, run_dir) for i, q in enumerate(questions, 1)]
        results = [job.result() for job in jobs]

    for _, text in results:
        print(text)
    failed = sum(1 for ok, _ in results if not ok)
    if failed:
        print(f"{failed} of {len(questions)} jobs FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
