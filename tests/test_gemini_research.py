"""Offline tests for the gemini-web-research scripts: no network, no agy."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "gemini-web-research" / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gr = load("gemini_research")
rp = load("read_page")

QUOTE = "Python 3.14 was released on October 7 2025"
GOOD_REPORT = {
    "answer": "Released 2025-10-07, see https://www.python.org/downloads/.",
    "claims": [{"claim": "release date", "url": "https://python.org/downloads", "quote": QUOTE}],
    "unconfirmed": ["EOL date"],
}


def make_tmpdir(case):
    tmp = tempfile.TemporaryDirectory()
    case.addCleanup(tmp.cleanup)
    return Path(tmp.name)


def tool_step(name, parameters, output):
    info = {"name": name, "parameters": parameters, "output": output}
    return {"event": "step_update", "step_update": {"step_type": "tool", "state": "DONE", "tool_info": info}}


def trace_lines(response=json.dumps(GOOD_REPORT), status="SUCCESS", search=True, read=True):
    events = []
    if search:
        events.append(tool_step("search_web", {"query": "python release"}, "results"))
    if read:
        cmd = f"python3 {gr.READER} 'https://www.python.org/downloads/#top'"
        events.append(tool_step("run_command", {"CommandLine": cmd}, f"x. {QUOTE}, and more."))
    events.append({"event": "result", "result": {"status": status, "response": response}})
    return "\n".join(["not json"] + [json.dumps(e) for e in events])


class Normalize(unittest.TestCase):
    def test_text(self):
        self.assertEqual(gr.normalize_text("  Hello,\nWORLD -- 3.14! "), "hello world 3 14")

    def test_url(self):
        self.assertEqual(gr.normalize_url("http://www.example.com/a/#frag"), "https://example.com/a")
        self.assertEqual(gr.normalize_url("https://example.com/a."), "https://example.com/a")


class ReadTrace(unittest.TestCase):
    def write(self, text):
        path = make_tmpdir(self) / "t.jsonl"
        path.write_text(text)
        return path

    def test_synthetic_trace(self):
        searches, opened, fetched, response, error = gr.read_trace(self.write(trace_lines()))
        self.assertEqual(searches, 1)
        self.assertEqual(opened, {"https://python.org/downloads"})
        self.assertIn(gr.normalize_text(QUOTE), fetched)
        self.assertEqual(json.loads(response)["unconfirmed"], ["EOL date"])
        self.assertIsNone(error)

    def test_error_status_and_ignored_commands(self):
        text = trace_lines(status="ERROR", read=False)
        other = tool_step("run_command", {"CommandLine": "ls"}, "files")
        _, opened, _, _, error = gr.read_trace(self.write(text + "\n" + json.dumps(other)))
        self.assertEqual(opened, set())
        self.assertEqual(error, "agy result status ERROR")

    def test_non_object_lines_are_skipped(self):
        self.assertEqual(gr.read_trace(self.write("1\n[]\n"))[0], 0)


class ClaimChecks(unittest.TestCase):
    opened = {"https://python.org/downloads"}
    fetched = gr.normalize_text(QUOTE + " plus more text")

    def check(self, **overrides):
        claim = dict(GOOD_REPORT["claims"][0], **overrides)
        return gr.check_claim(claim, self.opened, self.fetched)

    def test_ok(self):
        self.assertEqual(self.check(), [])

    def test_flags(self):
        self.assertEqual(self.check(url="https://other.org/"), ["URL was never read"])
        self.assertEqual(self.check(quote="too short"), ["quote is under 5 words"])
        self.assertEqual(self.check(quote="this quote is nowhere on the page"), ["quote not found in pages read"])

    def test_render_counts_flags(self):
        report = dict(GOOD_REPORT, answer="See https://never.read/x", claims=[])
        lines, flagged = gr.render_report(report, self.opened, self.fetched)
        self.assertEqual(flagged, 2)  # no claims + one unread URL in the answer
        self.assertIn("- https://never.read/x", lines)


class ParseReport(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(gr.parse_report(json.dumps(GOOD_REPORT)), GOOD_REPORT)

    def test_malformed(self):
        bad = [
            "not json", None, "[]", "{}",
            json.dumps(dict(GOOD_REPORT, claims="x")),
            json.dumps(dict(GOOD_REPORT, claims=[{"claim": "a"}])),
            json.dumps(dict(GOOD_REPORT, unconfirmed=[1])),
            json.dumps({k: v for k, v in GOOD_REPORT.items() if k != "answer"}),
        ]
        for response in bad:
            with self.subTest(response=response), self.assertRaises(ValueError):
                gr.parse_report(response)


class RunJob(unittest.TestCase):
    def run_job(self, trace_text=None, returncode=0, side_effect=None):
        run_dir = make_tmpdir(self)

        def fake_agy(question, trace_path, cwd):
            if side_effect:
                raise side_effect
            trace_path.write_text(trace_text)
            return returncode

        with mock.patch.object(gr, "run_agy", fake_agy):
            return gr.run_job(1, "when was Python 3.14 released?", run_dir)

    def test_ok(self):
        ok, text = self.run_job(trace_lines())
        self.assertTrue(ok)
        self.assertIn("[OK] release date", text)
        self.assertIn("Checks: 1 claims, 0 flagged.", text)

    def test_flagged_claim_still_succeeds(self):
        report = dict(GOOD_REPORT, claims=[dict(GOOD_REPORT["claims"][0], quote="a quote the page never had")])
        ok, text = self.run_job(trace_lines(json.dumps(report)))
        self.assertTrue(ok)
        self.assertIn("[FLAG (quote not found in pages read)]", text)

    def test_failed_paths(self):
        cases = {
            "no search": (dict(trace_text=trace_lines(search=False)), "no web search"),
            "no read": (dict(trace_text=trace_lines(read=False)), "read no pages"),
            "bad status": (dict(trace_text=trace_lines(status="ERROR")), "agy result status ERROR"),
            "exit code": (dict(trace_text=trace_lines(), returncode=3), "agy exited 3"),
            "malformed": (dict(trace_text=trace_lines(response='{"answer": 1}')), "FAILED"),
            "not json": (dict(trace_text=trace_lines(response="plain")), "not the required JSON"),
            "timeout": (dict(side_effect=subprocess.TimeoutExpired("agy", 1)), "did not finish"),
            "crash": (dict(side_effect=OSError("boom")), "unexpected OSError: boom"),
        }
        for name, (kwargs, expected) in cases.items():
            with self.subTest(name):
                ok, text = self.run_job(**kwargs)
                self.assertFalse(ok)
                self.assertIn("FAILED", text)
                self.assertIn(expected, text)


class ReadPage(unittest.TestCase):
    def test_extraction_skips_scripts_and_splits_blocks(self):
        html = "<html><head><title>t</title></head><body><script>x=1</script><h1>Title</h1><p>One  two</p><ul><li>a</li><li>b</li></ul></body></html>"
        self.assertEqual(rp.html_to_text(html), "Title\nOne two\na\nb")

    def test_scheme_rejected(self):
        for url in ("file:///etc/passwd", "ftp://example.com/x", "javascript:alert(1)", "example.com", "http://"):
            with self.subTest(url=url), self.assertRaises(SystemExit) as ctx:
                rp.check_url(url)
            self.assertIn("only http and https", str(ctx.exception))

    def test_http_urls_accepted(self):
        self.assertEqual(rp.check_url("https://example.com/a"), "https://example.com/a")

    def test_network_error_is_one_line(self):
        import urllib.error
        with mock.patch.object(rp.urllib.request, "urlopen", side_effect=urllib.error.URLError("down")):
            with self.assertRaises(SystemExit) as ctx:
                rp.fetch("https://example.com")
        self.assertEqual(str(ctx.exception), "read_page: cannot fetch https://example.com: down")


STALL_LOG = (
    "I1 mcp_manager.go:988] MCP: 2 server(s) still connecting after 30s: alpha, beta\n"
    "I1 mcp_manager.go:988] MCP: 1 server(s) still connecting after 1m0s: beta\n"
)


class Stall(unittest.TestCase):
    def test_diagnose_names_the_servers_still_connecting(self):
        trace = make_tmpdir(self) / "job-1.jsonl"
        self.assertEqual(gr.diagnose(trace), "")
        trace.with_suffix(".log").write_text("nothing relevant\n")
        self.assertEqual(gr.diagnose(trace), "")
        trace.with_suffix(".log").write_text(STALL_LOG)
        hint = gr.diagnose(trace)
        self.assertIn("connect: beta.", hint)
        self.assertIn("agy mcp disable", hint)

    def test_failed_job_carries_agy_error_and_hint(self):
        run_dir = make_tmpdir(self)
        line = json.dumps({"event": "result", "result": {"status": "ERROR", "error": "print timeout after 15m0s"}})

        def fake_agy(question, trace_path, cwd):
            trace_path.write_text(line + "\n")
            trace_path.with_suffix(".log").write_text(STALL_LOG)
            return 3

        with mock.patch.object(gr, "run_agy", fake_agy):
            ok, text = gr.run_job(1, "q", run_dir)
        self.assertFalse(ok)
        self.assertIn("agy result status ERROR: print timeout after 15m0s", text)
        self.assertIn("connect: beta.", text)

    def test_call_agy_bounds_the_turn_and_writes_a_log(self):
        trace = make_tmpdir(self) / "job-1.jsonl"
        with mock.patch.object(gr.subprocess, "run", return_value=mock.Mock(returncode=0)) as run:
            self.assertEqual(gr.call_agy("p", trace, trace.parent, 90, ["--x"]), 0)
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[cmd.index("--print-timeout") + 1], "90s")
        self.assertEqual(cmd[cmd.index("--log-file") + 1], str(trace.with_suffix(".log")))
        self.assertEqual(cmd[-1], "--x")
        self.assertEqual(run.call_args.kwargs["timeout"], 90 + gr.BACKSTOP_SECONDS)

    def probe(self, returncode=0, lines="", side_effect=None):
        def fake_call(prompt, trace_path, cwd, timeout, extra=()):
            trace_path.with_suffix(".log").write_text(STALL_LOG)
            if side_effect:
                raise side_effect
            trace_path.write_text(lines)
            return returncode

        with mock.patch.object(gr, "call_agy", fake_call):
            return gr.probe(make_tmpdir(self))

    def test_probe(self):
        ok_line = json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "ok"}})
        bad_line = json.dumps({"event": "result", "result": {"status": "ERROR", "error": "print timeout after 1m30s"}})
        self.assertIsNone(self.probe(lines=ok_line))
        self.assertIn("print timeout after 1m30s", self.probe(returncode=3, lines=bad_line))
        self.assertIn("agy exited 4", self.probe(returncode=4))
        reason = self.probe(side_effect=subprocess.TimeoutExpired("agy", 1))
        self.assertIn("no reply within", reason)
        self.assertIn("connect: beta.", reason)


class Main(unittest.TestCase):
    def test_failed_probe_exits_2_and_starts_no_job(self):
        with mock.patch.object(sys, "argv", ["x", "q"]), mock.patch.object(gr.shutil, "which", return_value="/bin/agy"), \
                mock.patch.object(gr, "probe", return_value="no reply"), mock.patch.object(gr, "run_job") as run_job, \
                mock.patch.object(sys, "stderr"), self.assertRaises(SystemExit) as ctx:
            gr.main()
        self.assertEqual(ctx.exception.code, 2)
        run_job.assert_not_called()

    def test_missing_agy_exits_2_before_launching(self):
        with mock.patch.object(sys, "argv", ["x", "q"]), mock.patch.object(gr.shutil, "which", return_value=None), \
                mock.patch.object(gr.subprocess, "run") as run, mock.patch.object(sys, "stderr"), \
                self.assertRaises(SystemExit) as ctx:
            gr.main()
        self.assertEqual(ctx.exception.code, 2)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
