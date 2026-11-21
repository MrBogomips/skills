"""Offline tests for gemini_editorial_review.py: no network, no API key.

Run from the repo root: python3 -m unittest discover -s tests -p 'test_*.py'
"""
import contextlib
import gc
import importlib.util
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "gemini-editorial-review" / "scripts" / "gemini_editorial_review.py"
FAKE_KEY = "AIzaSyFAKEFAKEFAKEFAKEFAKEFAKE0123456789"


def load():
    spec = importlib.util.spec_from_file_location("gemini_editorial_review", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


er = load()

ITALIAN = ("Il sistema permette di gestire gli utenti e di configurare le regole. "
           "Questo è un testo che non ha bisogno di essere tradotto, ma solo rivisto.")
ENGLISH = ("The system lets you manage the users and configure the rules. "
           "This is a text that does not need to be translated, only reviewed.")


def run_main(argv, env=None, stdin=None):
    """Run er.main(argv); return (exit code or None, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    code = None
    gc.collect()
    env = {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": "", "GEMINI_EDITORIAL_MODEL": "", **(env or {})}
    stdin_patch = mock.patch("sys.stdin", io.StringIO(stdin)) if stdin is not None \
        else contextlib.nullcontext()
    with mock.patch.dict(os.environ, env, clear=False), stdin_patch, \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            er.main(argv)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


def api_payload(revised, language="it", profile="technical", summary=("Tagliato il preambolo.",)):
    text = json.dumps({"language": language, "profile": profile, "revised": revised,
                       "summary": list(summary)})
    return {"status": "completed",
            "steps": [{"type": "thought", "content": []},
                      {"type": "model_output", "content": [{"type": "text", "text": text}]}]}


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
    queue = list(payloads)
    calls = []

    def _open(req, timeout=None, context=None):
        calls.append(json.loads(req.data.decode()))
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return FakeResponse(item)

    return _open, calls


class LanguageDetection(unittest.TestCase):
    def test_detects_italian_and_english(self):
        self.assertEqual(er.detect_language(ITALIAN), "it")
        self.assertEqual(er.detect_language(ENGLISH), "en")

    def test_ignores_code_blocks(self):
        text = "```\nthe and of to is in that it for\n```\n\n" + ITALIAN
        self.assertEqual(er.detect_language(text), "it")

    def test_unknown_or_too_short(self):
        self.assertIsNone(er.detect_language("ok"))
        self.assertIsNone(er.detect_language("Lorem ipsum dolor sit amet consectetur adipiscing elit"))


class ModelWarning(unittest.TestCase):
    def test_below_neon_warns(self):
        self.assertIn("below", er.model_warning("gemini-4-carbon"))
        self.assertIn("below", er.model_warning("models/gemini-4-hydrogen"))

    def test_neon_argon_and_unknown_ids_pass(self):
        self.assertEqual(er.model_warning("gemini-4-neon"), "")
        self.assertEqual(er.model_warning("gemini-4-argon"), "")
        self.assertEqual(er.model_warning("gemini-5-pro"), "")


class SystemInstruction(unittest.TestCase):
    def test_fixed_profile_sends_only_that_profile(self):
        text = er.system_instruction("technical", lang="it")
        self.assertIn("## Core rules", text)
        self.assertIn("## LLM tells", text)
        self.assertIn("## Workflow", text)
        self.assertIn("### technical", text)
        self.assertNotIn("### creative", text)
        self.assertNotIn("## Profile inference", text)
        self.assertIn("Language notes: Italian", text)

    def test_auto_profile_sends_all_profiles_and_inference(self):
        text = er.system_instruction("auto", lang=None)
        for profile in er.PROFILES:
            self.assertIn(f"### {profile}", text)
        self.assertIn("## Profile inference", text)
        self.assertNotIn("Language notes: Italian", text)

    def test_audience_rules_and_glossary(self):
        rules = [("AGENTS.md", "Never use the word leverage."), ("docs/style.md", "Use sentence case.")]
        text = er.system_instruction("blog", lang="en", audience="CTOs of small firms",
                                     rules=rules, glossary="tenant -> tenant")
        self.assertIn("Audience: CTOs of small firms", text)
        self.assertIn("## House rules", text)
        first = text.index("### From AGENTS.md")
        second = text.index("### From docs/style.md")
        self.assertLess(first, second)
        self.assertIn("Never use the word leverage.", text)
        self.assertIn("## Glossary\n\ntenant -> tenant", text)

    def test_no_rules_no_house_rules_section(self):
        self.assertNotIn("## House rules", er.system_instruction("auto", lang=None))


class Invariants(unittest.TestCase):
    SRC = ("---\ntitle: Guide\n---\n\n# Install\n\nRun `make build`, then open https://example.com/docs.\n\n"
           "## Notes\n\nHello {name}, you have <b>mail</b>.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
           "```bash\necho hi\n```\n")

    def test_reordered_headings_and_merged_table_pass(self):
        out = ("---\ntitle: Guide\n---\n\n## Notes\n\nHello {name}, you have <b>mail</b>.\n\n"
               "# Install\n\nOpen https://example.com/docs after `make build`.\n\n"
               "```bash\necho hi\n```\n")
        self.assertEqual(er.check_invariants(self.SRC, out), [])

    def test_changed_code_block(self):
        problems = er.check_invariants(self.SRC, self.SRC.replace("echo hi", "echo hello"))
        self.assertTrue(any("code block" in p for p in problems), problems)

    def test_lost_url_and_placeholder(self):
        out = self.SRC.replace("https://example.com/docs", "the docs").replace("{name}", "there")
        problems = er.check_invariants(self.SRC, out)
        self.assertTrue(any("URL" in p for p in problems), problems)
        self.assertTrue(any("{name}" in p for p in problems), problems)

    def test_changed_frontmatter(self):
        problems = er.check_invariants(self.SRC, self.SRC.replace("title: Guide", "title: The guide"))
        self.assertTrue(any("frontmatter" in p for p in problems), problems)

    def test_no_frontmatter_either_side(self):
        self.assertEqual(er.check_invariants("Some text.", "Some better text."), [])


class ResponseParsing(unittest.TestCase):
    def test_reads_json(self):
        result = er.parse_result(api_payload("Testo"))
        self.assertEqual(result["revised"], "Testo")
        self.assertEqual(result["summary"], ["Tagliato il preambolo."])

    def test_tolerates_a_json_fence(self):
        payload = api_payload("Testo")
        block = payload["steps"][1]["content"][0]
        block["text"] = "```json\n" + block["text"] + "\n```"
        self.assertEqual(er.parse_result(payload)["revised"], "Testo")

    def test_missing_field(self):
        payload = {"steps": [{"type": "model_output",
                              "content": [{"type": "text", "text": '{"revised": "x"}'}]}]}
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()) as err:
            er.parse_result(payload)
        self.assertIn("language", err.getvalue())

    def test_summary_must_be_a_list_of_strings(self):
        payload = api_payload("x")
        block = payload["steps"][1]["content"][0]
        data = json.loads(block["text"])
        data["summary"] = "not a list"
        block["text"] = json.dumps(data)
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()) as err:
            er.parse_result(payload)
        self.assertIn("summary", err.getvalue())


class Cli(unittest.TestCase):
    def test_usage_errors_exit_1(self):
        code, _, err = run_main(["--profile", "poetry", "-t", "x"])
        self.assertEqual(code, 1)
        self.assertIn("poetry", err)

    def test_missing_key_exits_2(self):
        code, _, err = run_main(["-t", ITALIAN])
        self.assertEqual(code, 2)
        self.assertIn("GEMINI_API_KEY", err)

    def test_empty_input(self):
        code, _, err = run_main([], stdin="  \n")
        self.assertEqual(code, 1)
        self.assertIn("empty", err)

    def test_too_long_input(self):
        code, _, err = run_main(["-t", "a " * (er.MAX_CHARS // 2 + 10)],
                                env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertEqual(code, 1)
        self.assertIn("split", err)

    def test_missing_rules_file(self):
        code, _, err = run_main(["-t", ITALIAN, "--rules", "/nonexistent/style.md", "--print-prompt"])
        self.assertEqual(code, 1)
        self.assertIn("/nonexistent/style.md", err)

    def test_print_prompt_needs_no_key_and_hides_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            rules = Path(tmp) / "style.md"
            rules.write_text("No exclamation marks.", encoding="utf-8")
            code, out, err = run_main(["-t", ITALIAN, "--rules", str(rules), "--print-prompt"],
                                      env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertIsNone(code, err)
        self.assertNotIn(FAKE_KEY, out)
        body = json.loads(out[out.index("{"):])
        self.assertEqual(body["model"], "gemini-4-neon")
        self.assertEqual(body["input"], ITALIAN)
        self.assertEqual(body["generation_config"]["thinking_level"], "high")
        self.assertIn("Language notes: Italian", body["system_instruction"])
        self.assertIn("No exclamation marks.", body["system_instruction"])
        self.assertIn("### From style.md", body["system_instruction"])

    def test_lang_flag_overrides_detection(self):
        code, out, _ = run_main(["-t", ENGLISH, "--lang", "it", "--print-prompt"])
        self.assertIsNone(code)
        self.assertIn("Language notes: Italian", out)

    def test_low_model_warns_but_runs(self):
        code, out, err = run_main(["-t", ITALIAN, "--model", "gemini-4-carbon", "--print-prompt"])
        self.assertIsNone(code)
        self.assertIn("below", err)
        self.assertIn('"model": "gemini-4-carbon"', out)

    def test_model_from_env(self):
        code, out, _ = run_main(["-t", ITALIAN, "--print-prompt"],
                                env={"GEMINI_EDITORIAL_MODEL": "gemini-4-argon"})
        self.assertIsNone(code)
        self.assertIn('"model": "gemini-4-argon"', out)

    def test_reviews_stdin_to_stdout_with_summary_on_stderr(self):
        opener, calls = fake_urlopen(api_payload("Testo rivisto {name}",
                                                 summary=("Uno.", "Due.")))
        with mock.patch.object(er.urllib.request, "urlopen", opener):
            code, out, err = run_main([], env={"GEMINI_API_KEY": FAKE_KEY},
                                      stdin="Testo originale {name}")
        self.assertIsNone(code, err)
        self.assertEqual(out, "Testo rivisto {name}\n")
        self.assertIn("language: it · profile: technical (inferred)", err)
        self.assertIn("- Uno.", err)
        self.assertIn("- Due.", err)
        self.assertEqual(len(calls), 1)

    def test_fixed_profile_not_marked_inferred(self):
        opener, _ = fake_urlopen(api_payload("x", profile="essay"))
        with mock.patch.object(er.urllib.request, "urlopen", opener):
            code, _, err = run_main(["-t", "y", "--profile", "essay"], env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertIsNone(code, err)
        self.assertIn("profile: essay", err)
        self.assertNotIn("inferred", err)

    def test_writes_output_file_and_refuses_the_source(self):
        opener, _ = fake_urlopen(api_payload("Rivisto\n"))
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "doc.md"
            src.write_text("Originale\n", encoding="utf-8")
            code, _, err = run_main(["-i", str(src), "-o", str(src)], env={"GEMINI_API_KEY": FAKE_KEY})
            self.assertEqual(code, 1)
            self.assertIn("overwrite", err)
            out_path = Path(tmp) / "doc.reviewed.md"
            with mock.patch.object(er.urllib.request, "urlopen", opener):
                code, out, err = run_main(["-i", str(src), "-o", str(out_path)],
                                          env={"GEMINI_API_KEY": FAKE_KEY})
            self.assertIsNone(code, err)
            self.assertEqual(out_path.read_text(encoding="utf-8"), "Rivisto\n")
            self.assertEqual(src.read_text(encoding="utf-8"), "Originale\n")

    def test_invariant_failure_keeps_the_text_in_unchecked(self):
        opener, _ = fake_urlopen(api_payload("Ciao Mario"))
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "out.md"
            with mock.patch.object(er.urllib.request, "urlopen", opener):
                code, _, err = run_main(["-t", "Ciao {name}", "-o", str(out_path)],
                                        env={"GEMINI_API_KEY": FAKE_KEY})
            self.assertEqual(code, 4)
            self.assertFalse(out_path.exists())
            self.assertEqual((Path(tmp) / "out.md.unchecked").read_text(encoding="utf-8"), "Ciao Mario")
            self.assertIn("{name}", err)

    def test_retries_once_on_5xx(self):
        error = urllib.error.HTTPError(er.ENDPOINT, 503, "busy", {}, io.BytesIO(b"{}"))
        opener, calls = fake_urlopen(error, api_payload("Ciao"))
        with mock.patch.object(er.urllib.request, "urlopen", opener):
            code, _, err = run_main(["-t", "Ciao"], env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertIsNone(code, err)
        self.assertEqual(len(calls), 2)

    def test_error_body_as_array_and_402_billing(self):
        body = json.dumps([{"error": {"code": 402, "message": "Your prepayment credits are depleted.",
                                      "status": "RESOURCE_EXHAUSTED"}}]).encode()
        error = urllib.error.HTTPError(er.ENDPOINT, 402, "Payment Required", {}, io.BytesIO(body))
        opener, _ = fake_urlopen(error)
        with mock.patch.object(er.urllib.request, "urlopen", opener):
            code, _, err = run_main(["-t", "Ciao"], env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertEqual(code, 1)
        self.assertIn("prepayment credits are depleted", err)
        self.assertIn("billing", err)

    def test_key_scrubbed_from_errors(self):
        body = json.dumps({"error": {"message": f"bad key {FAKE_KEY}"}}).encode()
        error = urllib.error.HTTPError(er.ENDPOINT, 400, "bad", {}, io.BytesIO(body))
        opener, _ = fake_urlopen(error)
        with mock.patch.object(er.urllib.request, "urlopen", opener):
            code, _, err = run_main(["-t", "Ciao"], env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertEqual(code, 1)
        self.assertNotIn(FAKE_KEY, err)


if __name__ == "__main__":
    unittest.main()
