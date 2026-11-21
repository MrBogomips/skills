"""Offline tests for the gemini-editorial-review scripts: no network, no API key, no real agy.

Run from the repo root: python3 -m unittest discover -s tests -p 'test_*.py'
"""
import contextlib
import gc
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "gemini-editorial-review" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import er_agy  # noqa: E402
import er_api  # noqa: E402
import er_config  # noqa: E402
import er_text  # noqa: E402
import gemini_editorial_review as cli  # noqa: E402

FAKE_KEY = "AIzaSyFAKEFAKEFAKEFAKEFAKEFAKE0123456789"
ITALIAN = ("Il sistema permette di gestire gli utenti e di configurare le regole. "
           "Questo è un testo che non ha bisogno di essere tradotto, ma solo rivisto.")
ENGLISH = ("The system lets you manage the users and configure the rules. "
           "This is a text that does not need to be translated, only reviewed.")
CLEAN_ENV = {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": "", "GEMINI_EDITORIAL_MODEL": "",
             "GEMINI_EDITORIAL_BACKEND": "", "XDG_CONFIG_HOME": ""}


def answer(revised, language="it", profile="technical", summary=("Tagliato il preambolo.",)):
    return json.dumps({"language": language, "profile": profile, "revised": revised, "summary": list(summary)})


def api_payload(revised, **kw):
    return {"status": "completed",
            "steps": [{"type": "thought", "content": []},
                      {"type": "model_output", "content": [{"type": "text", "text": answer(revised, **kw)}]}]}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def fake_urlopen(*payloads):
    """A urlopen stand-in returning the payloads in order; records the request bodies."""
    queue, calls = list(payloads), []

    def _open(req, timeout=None, context=None):
        calls.append(json.loads(req.data.decode()))
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return FakeResponse(item)

    return _open, calls


STARTED = {"event": "step_update", "step_update": {"step_index": 0, "state": "DONE", "step_type": "user_input"}}


def agy_lines(response, status="SUCCESS", started=True, error=None):
    events = [{"event": "init", "init": {"model": "m"}}] + ([STARTED] if started else [])
    result = {"status": status, "response": response}
    if error:
        result["error"] = error
    events.append({"event": "result", "result": result})
    return "not json\n" + "\n".join(json.dumps(e) for e in events) + "\n"


def fake_popen(lines, calls):
    """A Popen stand-in that writes `lines` to the trace file it is given and exits 0."""
    def _popen(cmd, cwd=None, stdout=None, **kw):
        calls.append({"cmd": cmd, "cwd": cwd, "kw": kw})
        stdout.write(lines)
        stdout.flush()
        proc = mock.Mock(returncode=0, pid=4242)
        proc.wait.return_value = 0
        return proc
    return _popen


class Isolated(unittest.TestCase):
    """Each test runs in an empty folder with its own user settings file."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        (self.tmp / "repo" / ".git").mkdir(parents=True)
        self.repo = self.tmp / "repo"
        self.user_file = self.tmp / "user" / "config.json"
        env = mock.patch.dict(os.environ, {**CLEAN_ENV, er_config.USER_ENV: str(self.user_file)})
        env.start()
        self.addCleanup(env.stop)
        old = os.getcwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, old)

    def run_main(self, argv, env=None, stdin=None):
        """Run cli.main(argv); return (exit code or None, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        code = None
        gc.collect()
        stdin_patch = mock.patch("sys.stdin", io.StringIO(stdin)) if stdin is not None \
            else contextlib.nullcontext()
        with mock.patch.dict(os.environ, env or {}), stdin_patch, \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                cli.main(argv)
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()


# --------------------------------------------------------------------------- #
# Shared text side.
# --------------------------------------------------------------------------- #
class LanguageDetection(unittest.TestCase):
    def test_detects_italian_and_english(self):
        self.assertEqual(er_text.detect_language(ITALIAN), "it")
        self.assertEqual(er_text.detect_language(ENGLISH), "en")

    def test_ignores_code_blocks(self):
        self.assertEqual(er_text.detect_language("```\nthe and of to is in that it for\n```\n\n" + ITALIAN), "it")

    def test_unknown_or_too_short(self):
        self.assertIsNone(er_text.detect_language("ok"))
        self.assertIsNone(er_text.detect_language("Lorem ipsum dolor sit amet consectetur adipiscing elit"))


class SystemInstruction(unittest.TestCase):
    def test_fixed_profile_sends_only_that_profile(self):
        text = er_text.system_instruction("technical", lang="it")
        for heading in ("## Core rules", "## LLM tells", "## Workflow", "### technical", "Language notes: Italian"):
            self.assertIn(heading, text)
        self.assertNotIn("### creative", text)
        self.assertNotIn("## Profile inference", text)

    def test_auto_profile_sends_all_profiles_and_inference(self):
        text = er_text.system_instruction("auto", lang=None)
        for profile in er_text.PROFILES:
            self.assertIn(f"### {profile}", text)
        self.assertIn("## Profile inference", text)
        self.assertNotIn("Language notes", text)

    def test_audience_rules_and_glossary(self):
        rules = [("AGENTS.md", "Never use the word leverage."), ("style.md", "Use sentence case.")]
        text = er_text.system_instruction("blog", lang="en", audience="CTOs", rules=rules, glossary="a -> b")
        self.assertIn("Audience: CTOs", text)
        self.assertLess(text.index("### From AGENTS.md"), text.index("### From style.md"))
        self.assertIn("## Glossary\n\na -> b", text)
        self.assertNotIn("## House rules", er_text.system_instruction("auto", lang=None))


class Invariants(unittest.TestCase):
    SRC = ("---\ntitle: Guide\n---\n\n# Install\n\nRun `make build`, then open https://example.com/docs.\n\n"
           "## Notes\n\nHello {name}, you have <b>mail</b>.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
           "```bash\necho hi\n```\n")

    def test_reordered_headings_and_merged_table_pass(self):
        out = ("---\ntitle: Guide\n---\n\n## Notes\n\nHello {name}, you have <b>mail</b>.\n\n"
               "# Install\n\nOpen https://example.com/docs after `make build`.\n\n```bash\necho hi\n```\n")
        self.assertEqual(er_text.check_invariants(self.SRC, out), [])

    def test_changed_code_url_placeholder_frontmatter(self):
        out = (self.SRC.replace("echo hi", "echo hello").replace("https://example.com/docs", "the docs")
               .replace("{name}", "there").replace("title: Guide", "title: The guide"))
        problems = " | ".join(er_text.check_invariants(self.SRC, out))
        for kind in ("code block", "URL", "{name}", "frontmatter"):
            self.assertIn(kind, problems)


class AnswerParsing(unittest.TestCase):
    def test_reads_json_and_tolerates_a_fence(self):
        self.assertEqual(er_text.parse_answer(answer("Testo"))["revised"], "Testo")
        self.assertEqual(er_text.parse_answer("```json\n" + answer("Testo") + "\n```")["revised"], "Testo")

    def test_missing_field_and_bad_summary(self):
        with self.assertRaisesRegex(er_text.ReviewError, "language"):
            er_text.parse_answer('{"revised": "x"}')
        bad = json.loads(answer("x"))
        bad["summary"] = "not a list"
        with self.assertRaisesRegex(er_text.ReviewError, "summary"):
            er_text.parse_answer(json.dumps(bad))


class ModelWarning(unittest.TestCase):
    def test_warnings(self):
        for model in ("gemini-4-carbon", "models/gemini-4-hydrogen", "gemini-4-hydrogen-high"):
            self.assertIn("below", cli.model_warning(model))
        self.assertIn("older", cli.model_warning("gemini-3.8-flash-high"))
        self.assertIn("not a Gemini model", cli.model_warning("claude-opus-5-5-high"))

    def test_neon_argon_and_unknown_gemini_pass(self):
        for model in ("gemini-4-neon", "gemini-4-argon", "gemini-4-neon-xhigh", "gemini-5-pro"):
            self.assertEqual(cli.model_warning(model), "")


# --------------------------------------------------------------------------- #
# Settings.
# --------------------------------------------------------------------------- #
class Settings(Isolated):
    def test_defaults(self):
        values = er_config.effective(self.repo)
        self.assertEqual(values["backend"], ("auto", "default"))
        self.assertEqual(values["api_model"][0], "gemini-4-neon")
        self.assertEqual(values["agy_model"][0], "gemini-4-neon-high")

    def test_project_overrides_user_and_env_overrides_both(self):
        er_config.set_value("user", "backend", "api", self.repo)
        sub = self.repo / "docs"
        sub.mkdir()
        er_config.set_value("project", "backend", "agy", sub)
        self.assertTrue((self.repo / er_config.PROJECT_FILE).is_file())  # written at the repository root
        self.assertEqual(er_config.effective(sub)["backend"][0], "agy")
        self.assertIn("project", er_config.effective(sub)["backend"][1])
        with mock.patch.dict(os.environ, {"GEMINI_EDITORIAL_BACKEND": "api"}):
            self.assertEqual(er_config.effective(sub)["backend"], ("api", "env GEMINI_EDITORIAL_BACKEND"))

    def test_validation(self):
        with self.assertRaisesRegex(er_text.ReviewError, "one of"):
            er_config.set_value("user", "backend", "carrier-pigeon", self.repo)
        with self.assertRaisesRegex(er_text.ReviewError, "positive"):
            er_config.set_value("user", "timeout", "0", self.repo)
        self.user_file.parent.mkdir(parents=True)
        self.user_file.write_text('{"colour": "blue"}')
        with self.assertRaisesRegex(er_text.ReviewError, "unknown setting"):
            er_config.effective(self.repo)

    def test_unset_removes_the_empty_file(self):
        er_config.set_value("user", "timeout", "60", self.repo)
        self.assertEqual(json.loads(self.user_file.read_text()), {"timeout": 60})
        er_config.unset_value("user", "timeout", self.repo)
        self.assertFalse(self.user_file.exists())

    def test_config_cli(self):
        code, out, err = self.run_main(["config", "set", "backend", "api", "--project"])
        self.assertIsNone(code, err)
        self.assertIn("backend = api", out)
        code, out, _ = self.run_main(["config"])
        self.assertIsNone(code)
        self.assertIn("backend = api    (project", out)
        self.assertIn("user file:", out)
        code, _, err = self.run_main(["config", "set", "colour", "blue"])
        self.assertEqual(code, 1)


# --------------------------------------------------------------------------- #
# Backend choice and the run.
# --------------------------------------------------------------------------- #
class BackendChoice(Isolated):
    def test_auto_prefers_agy_when_installed(self):
        with mock.patch.object(er_agy, "available", return_value=True):
            code, out, _ = self.run_main(["-t", ITALIAN, "--print-prompt"])
        self.assertIsNone(code)
        self.assertIn("# backend: agy · model: gemini-4-neon-high", out)
        self.assertIn("--disable-slash-commands", out)
        self.assertIn(er_agy.TEXT_START, out)

    def test_auto_falls_back_to_api(self):
        with mock.patch.object(er_agy, "available", return_value=False):
            code, out, _ = self.run_main(["-t", ITALIAN, "--print-prompt"], env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertIsNone(code)
        self.assertIn("# backend: api · model: gemini-4-neon", out)
        self.assertNotIn(FAKE_KEY, out)
        body = json.loads(out[out.index("{"):])
        self.assertEqual(body["generation_config"]["thinking_level"], "high")
        self.assertIn("Language notes: Italian", body["system_instruction"])

    def test_flag_beats_setting_and_model_env(self):
        er_config.set_value("user", "backend", "api", self.repo)
        code, out, _ = self.run_main(["-t", ITALIAN, "--via", "agy", "--print-prompt"],
                                     env={"GEMINI_EDITORIAL_MODEL": "gemini-4-argon-high"})
        self.assertIsNone(code)
        self.assertIn("# backend: agy · model: gemini-4-argon-high", out)

    def test_low_model_warns_but_runs(self):
        code, out, err = self.run_main(["-t", ITALIAN, "--via", "api", "--model", "gemini-4-carbon",
                                        "--print-prompt"])
        self.assertIsNone(code)
        self.assertIn("below", err)

    def test_rules_files_reach_the_prompt(self):
        rules = self.tmp / "style.md"
        rules.write_text("No exclamation marks.", encoding="utf-8")
        code, out, _ = self.run_main(["-t", ITALIAN, "--via", "api", "--rules", str(rules), "--print-prompt"])
        self.assertIsNone(code)
        self.assertIn("### From style.md", out)
        code, _, err = self.run_main(["-t", ITALIAN, "--rules", "/nonexistent/style.md", "--print-prompt"])
        self.assertEqual(code, 1)
        self.assertIn("/nonexistent/style.md", err)


class InputChecks(Isolated):
    def test_usage_errors_exit_1(self):
        code, _, err = self.run_main(["--profile", "poetry", "-t", "x"])
        self.assertEqual(code, 1)
        self.assertIn("poetry", err)

    def test_empty_and_too_long(self):
        code, _, err = self.run_main([], stdin="  \n")
        self.assertEqual((code, "empty" in err), (1, True))
        code, _, err = self.run_main(["-t", "a " * (er_text.MAX_CHARS // 2 + 10)])
        self.assertEqual((code, "split" in err), (1, True))

    def test_refuses_to_overwrite_the_source(self):
        src = self.tmp / "doc.md"
        src.write_text("Originale\n", encoding="utf-8")
        code, _, err = self.run_main(["--via", "api", "-i", str(src), "-o", str(src)],
                                     env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertEqual(code, 1)
        self.assertIn("overwrite", err)


class ApiBackend(Isolated):
    def run_api(self, argv, *payloads, key=FAKE_KEY, stdin=None):
        opener, calls = fake_urlopen(*payloads)
        with mock.patch.object(er_api.urllib.request, "urlopen", opener):
            result = self.run_main(["--via", "api", *argv], env={"GEMINI_API_KEY": key}, stdin=stdin)
        return (*result, calls)

    def test_missing_key_exits_2(self):
        code, _, err, _ = self.run_api(["-t", ITALIAN], key="")
        self.assertEqual(code, 2)
        self.assertIn("GEMINI_API_KEY", err)

    def test_reviews_stdin_to_stdout_with_summary(self):
        code, out, err, calls = self.run_api([], api_payload("Rivisto {name}", summary=("Uno.", "Due.")),
                                             stdin="Originale {name}")
        self.assertIsNone(code, err)
        self.assertEqual(out, "Rivisto {name}\n")
        self.assertIn("backend: api · model: gemini-4-neon", err)
        self.assertIn("language: it · profile: technical (inferred)", err)
        self.assertIn("- Due.", err)
        self.assertEqual(len(calls), 1)

    def test_writes_output_file(self):
        out_path = self.tmp / "out" / "doc.reviewed.md"
        code, out, err, _ = self.run_api(["-t", "x", "-o", str(out_path), "--profile", "essay"],
                                         api_payload("Rivisto\n", profile="essay"))
        self.assertIsNone(code, err)
        self.assertEqual(out_path.read_text(encoding="utf-8"), "Rivisto\n")
        self.assertNotIn("inferred", err)

    def test_invariant_failure_keeps_the_text_in_unchecked(self):
        out_path = self.tmp / "out.md"
        code, _, err, _ = self.run_api(["-t", "Ciao {name}", "-o", str(out_path)], api_payload("Ciao Mario"))
        self.assertEqual(code, 4)
        self.assertFalse(out_path.exists())
        self.assertEqual((self.tmp / "out.md.unchecked").read_text(encoding="utf-8"), "Ciao Mario")

    def test_retries_once_on_5xx(self):
        error = urllib.error.HTTPError(er_api.ENDPOINT, 503, "busy", {}, io.BytesIO(b"{}"))
        code, _, err, calls = self.run_api(["-t", "Ciao"], error, api_payload("Ciao"))
        self.assertIsNone(code, err)
        self.assertEqual(len(calls), 2)

    def test_error_body_as_array_402_and_key_scrubbed(self):
        body = json.dumps([{"error": {"code": 402, "message": f"Credits depleted for {FAKE_KEY}."}}]).encode()
        error = urllib.error.HTTPError(er_api.ENDPOINT, 402, "Payment Required", {}, io.BytesIO(body))
        code, _, err, _ = self.run_api(["-t", "Ciao"], error)
        self.assertEqual(code, 1)
        self.assertIn("Credits depleted", err)
        self.assertIn("billing", err)
        self.assertNotIn(FAKE_KEY, err)


class AgyBackend(Isolated):
    def run_agy(self, argv, lines, available=True):
        calls = []
        with mock.patch.object(er_agy, "available", return_value=available), \
                mock.patch.object(er_agy.subprocess, "Popen", fake_popen(lines, calls)), \
                mock.patch.object(er_agy.tempfile, "mkdtemp", return_value=str(self.tmp / "run")):
            (self.tmp / "run").mkdir(exist_ok=True)
            result = self.run_main(["--via", "agy", *argv])
        return (*result, calls)

    def test_reviews_through_one_isolated_turn(self):
        code, out, err, calls = self.run_agy(["-t", "Testo {name}"], agy_lines(answer("Rivisto {name}")))
        self.assertIsNone(code, err)
        self.assertEqual(out, "Rivisto {name}\n")
        self.assertIn("backend: agy · model: gemini-4-neon-high", err)
        cmd = calls[0]["cmd"]
        self.assertEqual(cmd[cmd.index("--model") + 1], "gemini-4-neon-high")
        self.assertEqual(json.loads(cmd[cmd.index("--json-schema") + 1]), er_text.RESPONSE_SCHEMA)
        deny = json.loads(cmd[cmd.index("--settings") + 1])["permissions"]["deny"]
        self.assertTrue({"mcp(*)", "write_file(*)", "command(*)"} <= set(deny))
        self.assertIn("--disable-slash-commands", cmd)
        self.assertTrue(calls[0]["kw"]["start_new_session"])
        self.assertEqual(Path(calls[0]["cwd"]).name, "workspace")
        prompt = cmd[cmd.index("-p") + 1]
        self.assertIn("## Core rules", prompt)
        self.assertIn(f"{er_agy.TEXT_START}\nTesto {{name}}\n{er_agy.TEXT_END}", prompt)
        self.assertFalse((self.tmp / "run").exists())  # removed after success

    def test_agy_missing_exits_2(self):
        code, _, err, calls = self.run_agy(["-t", "x"], "", available=False)
        self.assertEqual(code, 2)
        self.assertIn("agy not found", err)
        self.assertEqual(calls, [])

    def test_error_after_start_exits_1_and_keeps_the_trace(self):
        code, _, err, _ = self.run_agy(["-t", "x"], agy_lines(None, status="ERROR", error="quota exhausted"))
        self.assertEqual(code, 1)
        self.assertIn("agy result status ERROR: quota exhausted", err)
        self.assertTrue((self.tmp / "run" / "turn.jsonl").is_file())

    def test_turn_never_started_exits_2_with_the_mcp_hint(self):
        (self.tmp / "run").mkdir()
        (self.tmp / "run" / "turn.log").write_text("MCP: 1 server(s) still connecting after 30s: markitdown\n")
        code, _, err, _ = self.run_agy(["-t", "x"], agy_lines(None, status="ERROR", started=False,
                                                              error="print timeout"))
        self.assertEqual(code, 2)
        self.assertIn("markitdown", err)

    def test_bad_answer_exits_1(self):
        code, _, err, _ = self.run_agy(["-t", "x"], agy_lines("not json at all"))
        self.assertEqual(code, 1)
        self.assertIn("expected JSON", err)


class Watchdog(unittest.TestCase):
    def test_turn_that_never_starts_is_killed_with_its_group(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        run_dir = Path(tmp.name)
        proc = mock.Mock(pid=4242, returncode=None)
        proc.wait.side_effect = lambda timeout=None: (_ for _ in ()).throw(
            subprocess.TimeoutExpired("agy", timeout)) if timeout else None
        clock = iter(range(0, 100000, 10))
        with mock.patch.object(er_agy.subprocess, "Popen", return_value=proc), \
                mock.patch.object(er_agy.os, "killpg") as killpg, \
                mock.patch.object(er_agy.time, "monotonic", lambda: next(clock)):
            with self.assertRaises(er_agy.TurnNotStarted):
                er_agy.call_agy("p", "m", run_dir, 900)
        killpg.assert_called_once_with(4242, er_agy.signal.SIGKILL)


if __name__ == "__main__":
    unittest.main()
