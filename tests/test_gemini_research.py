"""Offline tests for the gemini-web-research scripts: no network, no agy."""

import importlib.util
import io
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


INIT = {"event": "init", "init": {"model": "m"}}
STARTED = {"event": "step_update", "step_update": {"step_index": 0, "state": "DONE", "step_type": "user_input"}}


def trace_lines(response=json.dumps(GOOD_REPORT), status="SUCCESS", search=True, read=True):
    events = [INIT, STARTED]
    if search:
        events.append(tool_step("search_web", {"query": "python release"}, "results"))
    if read:
        cmd = f"python3 {gr.READER.name} 'https://www.python.org/downloads/#top'"
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
            trace_path.write_text(trace_text)
            if side_effect:
                raise side_effect
            return returncode

        with mock.patch.object(gr, "run_agy", fake_agy):
            return gr.run_job(1, "when was Python 3.14 released?", run_dir)

    def test_ok(self):
        status, text = self.run_job(trace_lines())
        self.assertEqual(status, gr.OK)
        self.assertIn("[OK] release date", text)
        self.assertIn("Checks: 1 claims, 0 flagged.", text)

    def test_flagged_claim_still_succeeds(self):
        report = dict(GOOD_REPORT, claims=[dict(GOOD_REPORT["claims"][0], quote="a quote the page never had")])
        status, text = self.run_job(trace_lines(json.dumps(report)))
        self.assertEqual(status, gr.OK)
        self.assertIn("[FLAG (quote not found in pages read)]", text)

    def test_failed_paths(self):
        cases = {
            "no search": (dict(trace_text=trace_lines(search=False)), "no web search"),
            "no read": (dict(trace_text=trace_lines(read=False)), "read no pages"),
            "bad status": (dict(trace_text=trace_lines(status="ERROR")), "agy result status ERROR"),
            "exit code": (dict(trace_text=trace_lines(), returncode=3), "agy exited 3"),
            "malformed": (dict(trace_text=trace_lines(response='{"answer": 1}')), "FAILED"),
            "not json": (dict(trace_text=trace_lines(response="plain")), "not the required JSON"),
            "timeout": (dict(trace_text=trace_lines(), side_effect=subprocess.TimeoutExpired("agy", 1)), "did not finish"),
            "crash": (dict(trace_text=trace_lines(), side_effect=OSError("boom")), "unexpected OSError: boom"),
        }
        for name, (kwargs, expected) in cases.items():
            with self.subTest(name):
                status, text = self.run_job(**kwargs)
                self.assertEqual(status, gr.FAILED)
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
        self.assertIn("agy mcp remove", hint)

    def test_failed_job_carries_agy_error_and_hint(self):
        run_dir = make_tmpdir(self)
        line = json.dumps({"event": "result", "result": {"status": "ERROR", "error": "print timeout after 15m0s"}})

        def fake_agy(question, trace_path, cwd):
            trace_path.write_text(line + "\n")
            trace_path.with_suffix(".log").write_text(STALL_LOG)
            return 3

        with mock.patch.object(gr, "run_agy", fake_agy):
            status, text = gr.run_job(1, "q", run_dir)
        self.assertEqual(status, gr.SETUP)  # the turn never started
        self.assertIn("agy result status ERROR: print timeout after 15m0s", text)
        self.assertIn("connect: beta.", text)

    def test_call_agy_bounds_the_turn_and_writes_a_log(self):
        trace = make_tmpdir(self) / "job-1.jsonl"
        proc = mock.Mock(returncode=0)
        proc.wait.return_value = 0
        with mock.patch.object(gr.subprocess, "Popen", return_value=proc) as popen:
            self.assertEqual(gr.call_agy("p", trace, trace.parent, 90, ["--x"]), 0)
        cmd = popen.call_args.args[0]
        self.assertEqual(cmd[cmd.index("--print-timeout") + 1], "90s")
        self.assertEqual(cmd[cmd.index("--log-file") + 1], str(trace.with_suffix(".log")))
        self.assertEqual(cmd[-1], "--x")
        self.assertIn("--disable-slash-commands", cmd)
        settings = json.loads(cmd[cmd.index("--settings") + 1])
        self.assertEqual(settings["toolPermission"], "always-proceed")
        self.assertTrue({"mcp(*)", "write_file(*)", "command(curl)"} <= set(settings["permissions"]["deny"]))
        self.assertNotIn("--sandbox", cmd)

    def test_job_prompt_names_the_reader_relative_to_the_workspace(self):
        trace = make_tmpdir(self) / "job-1.jsonl"
        with mock.patch.object(gr, "call_agy", return_value=0) as call:
            gr.run_agy("q?", trace, trace.parent)
        prompt = call.call_args.args[0]
        self.assertIn("python3 read_page.py '<url>'", prompt)
        self.assertNotIn(str(gr.READER.parent), prompt)



class Watchdog(unittest.TestCase):
    """call_agy kills a turn that never starts, and a turn that outlives its timeout."""

    def fake_popen(self, trace, lines, finishes_after):
        """A process that writes `lines` to the trace and exits after `finishes_after` polls (None: never)."""
        proc = mock.Mock(returncode=None)
        polls = {"n": 0}

        def wait(timeout=None):
            if timeout is None:
                return proc.returncode
            polls["n"] += 1
            trace.write_text(lines)
            if finishes_after is not None and polls["n"] >= finishes_after:
                proc.returncode = 0
                return 0
            raise subprocess.TimeoutExpired("agy", timeout)

        proc.wait.side_effect = wait
        proc.kill.side_effect = lambda: setattr(proc, "returncode", -9)
        return proc

    def call(self, lines, finishes_after, timeout=900):
        trace = make_tmpdir(self) / "job-1.jsonl"
        trace.with_suffix(".log").write_text(STALL_LOG)
        proc = self.fake_popen(trace, lines, finishes_after)
        proc.pid = 4242
        clock = iter(range(0, 100000, 10))  # every poll advances 10 seconds
        with mock.patch.object(gr.subprocess, "Popen", return_value=proc) as popen, \
                mock.patch.object(gr.os, "killpg") as killpg, \
                mock.patch.object(gr.time, "monotonic", lambda: next(clock)):
            try:
                return gr.call_agy("p", trace, trace.parent, timeout), proc
            finally:
                self.assertTrue(popen.call_args.kwargs["start_new_session"])
                self.killpg = killpg

    def test_turn_that_never_starts_is_killed_with_its_children(self):
        with self.assertRaises(gr.TurnNotStarted):
            self.call(json.dumps(INIT) + "\n", finishes_after=None)
        self.killpg.assert_called_once_with(4242, gr.signal.SIGKILL)

    def test_started_turn_is_not_killed_by_the_start_watchdog(self):
        returncode, proc = self.call(trace_lines(), finishes_after=20)
        self.assertEqual(returncode, 0)
        self.killpg.assert_not_called()

    def test_backstop_kills_a_turn_past_its_timeout(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            self.call(trace_lines(), finishes_after=None, timeout=30)

    def test_finished_process_leaves_the_live_set(self):
        self.call(trace_lines(), finishes_after=1)
        self.assertEqual(gr.LIVE, set())

    def test_kill_all_kills_every_live_group_and_blocks_new_launches(self):
        procs = [mock.Mock(pid=n) for n in (11, 12)]
        trace = make_tmpdir(self) / "job-1.jsonl"
        with mock.patch.object(gr, "LIVE", set(procs)), mock.patch.object(gr, "STOPPING", gr.threading.Event()), \
                mock.patch.object(gr.os, "killpg") as killpg, mock.patch.object(gr.subprocess, "Popen") as popen:
            gr.kill_all()
            with self.assertRaises(gr.RoundStopped):
                gr.call_agy("p", trace, trace.parent, 900)
        self.assertEqual(sorted(c.args[0] for c in killpg.call_args_list), [11, 12])
        for proc in procs:
            proc.wait.assert_called_once_with()
        popen.assert_not_called()

    def test_watcher_error_kills_agy(self):
        trace = make_tmpdir(self) / "job-1.jsonl"
        proc = mock.Mock(pid=4242)
        with mock.patch.object(gr.subprocess, "Popen", return_value=proc), \
                mock.patch.object(gr, "watch", side_effect=OSError("trace unreadable")), \
                mock.patch.object(gr.os, "killpg") as killpg, self.assertRaises(OSError):
            gr.call_agy("p", trace, trace.parent, 900)
        killpg.assert_called_once_with(4242, gr.signal.SIGKILL)
        self.assertNotIn(proc, gr.LIVE)

    def test_turn_started(self):
        trace = make_tmpdir(self) / "t.jsonl"
        self.assertFalse(gr.turn_started(trace))
        trace.write_text(json.dumps(INIT) + "\nnot json\n")
        self.assertFalse(gr.turn_started(trace))
        trace.write_text(trace_lines())
        self.assertTrue(gr.turn_started(trace))


class SetupFailure(unittest.TestCase):
    """A job whose agy turn never started is an agy setup failure, not a research failure."""

    def run_job(self, fake):
        with mock.patch.object(gr, "run_agy", fake):
            return gr.run_job(1, "q", make_tmpdir(self))

    def test_stalled_turn_names_the_mcp_servers(self):
        def fake(question, trace_path, cwd):
            trace_path.with_suffix(".log").write_text(STALL_LOG)
            raise gr.TurnNotStarted()

        status, text = self.run_job(fake)
        self.assertEqual(status, gr.SETUP)
        self.assertIn(f"did not start within {gr.START_TIMEOUT_SECONDS}s", text)
        self.assertIn("connect: beta.", text)

    def test_agy_error_before_the_turn_is_setup(self):
        error = json.dumps({"event": "result", "result": {"status": "ERROR", "error": "invalid model selection"}})

        def fake(question, trace_path, cwd):
            trace_path.write_text("Error: invalid model selection\n" + error + "\n")
            return 1

        status, text = self.run_job(fake)
        self.assertEqual(status, gr.SETUP)
        self.assertIn("invalid model selection", text)

    def test_error_after_the_turn_started_is_a_job_failure(self):
        def fake(question, trace_path, cwd):
            trace_path.write_text(trace_lines(status="ERROR"))
            return 3

        self.assertEqual(self.run_job(fake)[0], gr.FAILED)


class Main(unittest.TestCase):
    def main(self, results):
        with mock.patch.object(sys, "argv", ["x"] + [f"q{i}" for i in range(len(results))]), \
                mock.patch.object(gr.shutil, "which", return_value="/bin/agy"), \
                mock.patch.object(gr.tempfile, "mkdtemp", return_value=str(make_tmpdir(self))), \
                mock.patch.object(gr, "STOPPING", gr.threading.Event()), \
                mock.patch.object(gr, "run_job", side_effect=results) as run_job, \
                mock.patch.object(gr.subprocess, "run") as run, \
                mock.patch.object(gr.subprocess, "Popen") as popen, \
                mock.patch.object(sys, "stdout", new_callable=io.StringIO) as out, \
                mock.patch.object(sys, "stderr", new_callable=io.StringIO) as err:
            try:
                gr.main()
                code = 0
            except SystemExit as exc:
                code = exc.code
            finally:
                handlers = {n: gr.signal.getsignal(n) for n in (gr.signal.SIGTERM, gr.signal.SIGHUP)}
                for signum in handlers:
                    gr.signal.signal(signum, gr.signal.SIG_DFL)
        self.assertEqual(set(handlers.values()), {gr.on_signal})
        run.assert_not_called()  # no test turn to agy before the jobs
        popen.assert_not_called()
        self.assertEqual(run_job.call_count, len(results))
        return code, out.getvalue(), err.getvalue()

    def test_all_jobs_ok_exits_0(self):
        code, out, _ = self.main([(gr.OK, "report 1"), (gr.OK, "report 2")])
        self.assertEqual(code, 0)
        self.assertIn("report 2", out)

    def test_some_failed_exits_1(self):
        code, out, _ = self.main([(gr.OK, "report 1"), (gr.FAILED, "FAILED: x")])
        self.assertEqual(code, 1)
        self.assertIn("1 of 2 jobs FAILED", out)

    def test_every_job_failing_at_setup_exits_2_with_one_reason(self):
        code, out, err = self.main([(gr.SETUP, "FAILED: stalled on beta"), (gr.SETUP, "FAILED: stalled on beta")])
        self.assertEqual(code, 2)
        self.assertIn("agy could not start a turn", err)
        self.assertIn("Stalled on beta", err)
        self.assertIn("do not retry", err.lower())
        self.assertEqual(out.count("stalled on beta"), 0)

    def test_interrupt_stops_running_jobs(self):
        with mock.patch.object(gr, "kill_all") as kill_all, self.assertRaises(KeyboardInterrupt):
            self.main([KeyboardInterrupt()])
        kill_all.assert_called_once_with()

    def test_signal_handler_exits_with_the_conventional_status(self):
        with self.assertRaises(SystemExit) as ctx:
            gr.on_signal(gr.signal.SIGTERM, None)
        self.assertEqual(ctx.exception.code, 128 + gr.signal.SIGTERM)

    def test_mixed_setup_and_ok_exits_1(self):
        code, _, _ = self.main([(gr.OK, "report 1"), (gr.SETUP, "FAILED: stalled")])
        self.assertEqual(code, 1)

    def test_missing_agy_exits_2_before_launching(self):
        with mock.patch.object(sys, "argv", ["x", "q"]), mock.patch.object(gr.shutil, "which", return_value=None), \
                mock.patch.object(gr.subprocess, "run") as run, mock.patch.object(sys, "stderr"), \
                self.assertRaises(SystemExit) as ctx:
            gr.main()
        self.assertEqual(ctx.exception.code, 2)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
