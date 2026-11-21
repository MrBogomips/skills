"""Offline tests for gemini_translate.py: no network, no API key.

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
SCRIPT = ROOT / "skills" / "gemini-translate" / "scripts" / "gemini_translate.py"
FAKE_KEY = "AIzaSyFAKEFAKEFAKEFAKEFAKEFAKE0123456789"


def load():
    spec = importlib.util.spec_from_file_location("gemini_translate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gt = load()


def run_main(argv, env=None, stdin=None):
    """Run gt.main(argv); return (exit code or None, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    code = None
    gc.collect()
    env = {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": "", **(env or {})}
    stdin_patch = mock.patch("sys.stdin", io.StringIO(stdin)) if stdin is not None \
        else contextlib.nullcontext()
    with mock.patch.dict(os.environ, env, clear=False), stdin_patch, \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            gt.main(argv)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


def api_payload(translation, source="en", target="it", register="technical"):
    text = json.dumps({"source_language": source, "target_language": target,
                       "register": register, "translation": translation})
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


class LanguageCodes(unittest.TestCase):
    def test_codes_and_names(self):
        self.assertEqual(gt.language_code("it"), "it")
        self.assertEqual(gt.language_code("it-IT"), "it")
        self.assertEqual(gt.language_code("pt_BR"), "pt")
        self.assertEqual(gt.language_code("Italian"), "it")
        self.assertEqual(gt.language_code("italiano"), "it")
        self.assertEqual(gt.language_code("Deutsch"), "de")
        self.assertIsNone(gt.language_code("Klingon"))


class SystemInstruction(unittest.TestCase):
    def test_fixed_register_sends_only_that_profile(self):
        text = gt.system_instruction("Italian", "technical")
        self.assertIn("Core rules", text)
        self.assertIn("Target language: Italian", text)
        self.assertIn("one action per step", text)
        self.assertNotIn("conversational, warm", text)
        self.assertNotIn("Register inference", text)
        self.assertIn("Target language notes: Italian", text)

    def test_auto_register_sends_all_profiles_and_inference(self):
        text = gt.system_instruction("de", "auto")
        self.assertIn("conversational, warm", text)
        self.assertIn("one action per step", text)
        self.assertIn("Register inference", text)
        self.assertNotIn("Target language notes: Italian", text)

    def test_glossary_pins_and_review(self):
        text = gt.system_instruction("it", "formal", glossary="cloud -> cloud",
                                     pinned_source="en", review=True)
        self.assertIn("## Glossary\n\ncloud -> cloud", text)
        self.assertIn("The source language is en", text)
        self.assertIn("revision pass", text)
        self.assertNotIn("revision pass", gt.system_instruction("it", "formal"))


class Chunking(unittest.TestCase):
    def test_short_text_is_one_chunk(self):
        self.assertEqual(gt.split_chunks("# A\n\nhello\n", 1000), ["# A\n\nhello\n"])

    def test_splits_at_headings_and_rejoins_exactly(self):
        text = "# One\n\n" + "a " * 40 + "\n\n## Two\n\n" + "b " * 40 + "\n\n## Three\n\nc\n"
        chunks = gt.split_chunks(text, 120)
        self.assertGreater(len(chunks), 1)
        self.assertEqual("".join(chunks), text)
        for chunk in chunks[1:]:
            self.assertTrue(chunk.startswith("#"))

    def test_never_splits_inside_a_fence(self):
        fence = "```\n# not a heading\n" + "x\n\n" * 50 + "```\n"
        text = "# A\n\nintro\n\n" + fence + "\n## B\n\nend\n"
        chunks = gt.split_chunks(text, 60)
        self.assertEqual("".join(chunks), text)
        self.assertTrue(any(fence in chunk for chunk in chunks))


class Invariants(unittest.TestCase):
    SRC = ("# Install\n\nRun `make build`, then open https://example.com/docs.\n\n"
           "Hello {name}, you have %d new <b>messages</b>.\n\n"
           "| a | b |\n|---|---|\n| 1 | 2 |\n\n```bash\necho hi\n```\n")
    GOOD = ("# Installazione\n\nEsegui `make build`, poi apri https://example.com/docs.\n\n"
            "Ciao {name}, hai %d nuovi <b>messaggi</b>.\n\n"
            "| a | b |\n|---|---|\n| 1 | 2 |\n\n```bash\necho hi\n```\n")

    def test_good_translation_passes(self):
        self.assertEqual(gt.check_invariants(self.SRC, self.GOOD), [])

    def test_dropped_placeholder(self):
        problems = gt.check_invariants(self.SRC, self.GOOD.replace("{name}", "Mario"))
        self.assertTrue(any("{name}" in p for p in problems), problems)

    def test_changed_code_block(self):
        problems = gt.check_invariants(self.SRC, self.GOOD.replace("echo hi", "echo ciao"))
        self.assertTrue(any("code block" in p for p in problems), problems)

    def test_translated_inline_code(self):
        problems = gt.check_invariants(self.SRC, self.GOOD.replace("`make build`", "`crea build`"))
        self.assertTrue(any("inline code" in p for p in problems), problems)

    def test_lost_heading_and_table_row(self):
        broken = self.GOOD.replace("# Installazione\n", "Installazione\n").replace("| 1 | 2 |\n", "")
        problems = gt.check_invariants(self.SRC, broken)
        self.assertTrue(any("heading" in p for p in problems), problems)
        self.assertTrue(any("table" in p for p in problems), problems)

    def test_url_and_tag(self):
        broken = self.GOOD.replace("https://example.com/docs", "example.com").replace("<b>", "")
        problems = gt.check_invariants(self.SRC, broken)
        self.assertTrue(any("URL" in p for p in problems), problems)
        self.assertTrue(any("tag" in p for p in problems), problems)

    def test_longer_closing_fence_does_not_swallow_prose(self):
        src = "```\nx\n````\n\nSee {name} here.\n\n~~~\ny\n~~~\n"
        out = "```\nx\n````\n\nVedi {name} qui.\n\n~~~\ny\n~~~\n"
        self.assertEqual(gt.check_invariants(src, out), [])

    def test_translated_code_comment_is_flagged(self):
        src = "```python\n# compute total\nx = 1\n```\n"
        problems = gt.check_invariants(src, src.replace("compute total", "calcola il totale"))
        self.assertTrue(any("code block" in p for p in problems), problems)

    def test_prose_percent_is_not_a_placeholder(self):
        self.assertEqual(gt.check_invariants("Save 50% today.", "Risparmia il 50% oggi."), [])


class ResponseParsing(unittest.TestCase):
    def test_reads_json_from_model_output(self):
        result = gt.parse_result(api_payload("Ciao"))
        self.assertEqual(result["translation"], "Ciao")
        self.assertEqual(result["source_language"], "en")

    def test_tolerates_a_json_fence(self):
        payload = api_payload("Ciao")
        block = payload["steps"][1]["content"][0]
        block["text"] = "```json\n" + block["text"] + "\n```"
        self.assertEqual(gt.parse_result(payload)["translation"], "Ciao")

    def test_no_text_names_the_status(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()) as err:
            gt.parse_result({"status": "failed", "steps": []})
        self.assertIn("failed", err.getvalue())

    def test_missing_field(self):
        payload = {"steps": [{"type": "model_output",
                              "content": [{"type": "text", "text": '{"translation": "x"}'}]}]}
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()) as err:
            gt.parse_result(payload)
        self.assertIn("source_language", err.getvalue())


class Cli(unittest.TestCase):
    def test_usage_errors_exit_1_not_2(self):
        code, _, _ = run_main(["-t", "Hello"])
        self.assertEqual(code, 1)          # exit 2 is reserved for a missing key
        code, _, err = run_main(["--to", "it", "--register", "business", "-t", "x"])
        self.assertEqual(code, 1)
        self.assertIn("business", err)

    def test_regional_target_skips_the_same_language_guard(self):
        opener, _ = fake_urlopen(api_payload("Olá equipe", source="pt", target="pt"))
        with mock.patch.object(gt.urllib.request, "urlopen", opener):
            code, out, err = run_main(["--to", "pt-BR", "-t", "Olá equipa"],
                                      env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertIsNone(code, err)
        self.assertEqual(out, "Olá equipe\n")

    def test_no_input(self):
        code, _, err = run_main(["--to", "it"], stdin="")
        self.assertEqual(code, 1)
        self.assertIn("nothing to translate", err)

    def test_text_and_input_conflict(self):
        code, _, err = run_main(["--to", "it", "-t", "x", "-i", "y.md"])
        self.assertEqual(code, 1)
        self.assertIn("not both", err)

    def test_missing_key_exits_2(self):
        code, _, err = run_main(["--to", "it", "-t", "Hello"])
        self.assertEqual(code, 2)
        self.assertIn("GEMINI_API_KEY", err)

    def test_print_prompt_needs_no_key_and_hides_it(self):
        code, out, _ = run_main(["--to", "it", "--register", "technical", "-t", "Hello",
                                 "--print-prompt"], env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertIsNone(code)
        self.assertNotIn(FAKE_KEY, out)
        body = json.loads(out[out.index("{"):])
        self.assertEqual(body["model"], gt.DEFAULT_MODEL)
        self.assertEqual(body["input"], "Hello")
        self.assertEqual(body["generation_config"]["thinking_level"], "medium")
        self.assertEqual(body["response_format"]["mime_type"], "application/json")
        self.assertIn("Target language notes: Italian", body["system_instruction"])

    def test_model_from_env(self):
        code, out, _ = run_main(["--to", "it", "-t", "Hi", "--print-prompt"],
                                env={"GEMINI_TRANSLATE_MODEL": "gemini-x"})
        self.assertIsNone(code)
        self.assertIn('"model": "gemini-x"', out)

    def test_translates_stdin_to_stdout(self):
        opener, calls = fake_urlopen(api_payload("Ciao {name}"))
        with mock.patch.object(gt.urllib.request, "urlopen", opener):
            code, out, err = run_main(["--to", "it"], env={"GEMINI_API_KEY": FAKE_KEY},
                                      stdin="Hello {name}")
        self.assertIsNone(code, err)
        self.assertEqual(out, "Ciao {name}\n")
        self.assertIn("source: en", err)
        self.assertIn("register: technical (inferred)", err)
        self.assertEqual(len(calls), 1)

    def test_writes_output_file(self):
        opener, _ = fake_urlopen(api_payload("Ciao\n"))
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "sub" / "out.md"
            with mock.patch.object(gt.urllib.request, "urlopen", opener):
                code, out, err = run_main(["--to", "it", "-t", "Hello\n", "-o", str(out_path)],
                                          env={"GEMINI_API_KEY": FAKE_KEY})
            self.assertIsNone(code, err)
            self.assertEqual(out_path.read_text(encoding="utf-8"), "Ciao\n")
            self.assertIn(str(out_path), out)

    def test_same_language_exits_3(self):
        opener, _ = fake_urlopen(api_payload("Ciao", source="it"))
        with mock.patch.object(gt.urllib.request, "urlopen", opener):
            code, out, err = run_main(["--to", "it", "-t", "Ciao"],
                                      env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertEqual(code, 3)
        self.assertEqual(out, "")
        self.assertIn("already", err)

    def test_invariant_failure_keeps_the_text_in_unchecked(self):
        opener, _ = fake_urlopen(api_payload("Ciao Mario"))
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "out.md"
            with mock.patch.object(gt.urllib.request, "urlopen", opener):
                code, _, err = run_main(["--to", "it", "-t", "Hello {name}", "-o", str(out_path)],
                                        env={"GEMINI_API_KEY": FAKE_KEY})
            self.assertEqual(code, 4)
            self.assertFalse(out_path.exists())
            self.assertEqual((Path(tmp) / "out.md.unchecked").read_text(encoding="utf-8"),
                             "Ciao Mario")
            self.assertIn("{name}", err)

    def test_review_makes_a_second_call_with_source_and_draft(self):
        opener, calls = fake_urlopen(api_payload("bozza"), api_payload("finale"))
        with mock.patch.object(gt.urllib.request, "urlopen", opener):
            code, out, err = run_main(["--to", "it", "-t", "draft me", "--review"],
                                      env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertIsNone(code, err)
        self.assertEqual(out, "finale\n")
        self.assertEqual(len(calls), 2)
        self.assertIn("draft me", calls[1]["input"])
        self.assertIn("bozza", calls[1]["input"])
        self.assertIn("revision pass", calls[1]["system_instruction"])

    def test_chunks_pin_source_and_register(self):
        text = "# A\n\n" + "a " * 30 + "\n\n# B\n\n" + "b " * 30 + "\n"
        opener, calls = fake_urlopen(api_payload("# A'\n\nx\n\n", register="informal"),
                                     api_payload("# B'\n\ny\n", register="informal"))
        with mock.patch.object(gt.urllib.request, "urlopen", opener):
            code, out, err = run_main(["--to", "it", "-t", text, "--chunk-chars", "80"],
                                      env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertIsNone(code, err)
        self.assertEqual(out, "# A'\n\nx\n\n# B'\n\ny\n")
        self.assertEqual(len(calls), 2)
        self.assertIn("Register inference", calls[0]["system_instruction"])
        self.assertNotIn("Register inference", calls[1]["system_instruction"])
        self.assertIn("conversational, warm", calls[1]["system_instruction"])
        self.assertIn("The source language is en", calls[1]["system_instruction"])

    def test_retries_once_on_5xx(self):
        error = urllib.error.HTTPError(gt.ENDPOINT, 503, "busy", {}, io.BytesIO(b"{}"))
        opener, calls = fake_urlopen(error, api_payload("Ciao"))
        with mock.patch.object(gt.urllib.request, "urlopen", opener):
            code, out, err = run_main(["--to", "it", "-t", "Hello"],
                                      env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertIsNone(code, err)
        self.assertEqual(len(calls), 2)

    def test_error_body_as_array_and_402_billing(self):
        body = json.dumps([{"error": {"code": 402, "message": "Credits depleted."}}]).encode()
        error = urllib.error.HTTPError(gt.ENDPOINT, 402, "Payment Required", {}, io.BytesIO(body))
        opener, _ = fake_urlopen(error)
        with mock.patch.object(gt.urllib.request, "urlopen", opener):
            code, _, err = run_main(["--to", "it", "-t", "Hello"], env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertEqual(code, 1)
        self.assertIn("Credits depleted.", err)
        self.assertIn("billing", err)

    def test_key_scrubbed_from_errors(self):
        body = json.dumps({"error": {"message": f"bad key {FAKE_KEY}"}}).encode()
        error = urllib.error.HTTPError(gt.ENDPOINT, 400, "bad", {}, io.BytesIO(body))
        opener, _ = fake_urlopen(error)
        with mock.patch.object(gt.urllib.request, "urlopen", opener):
            code, _, err = run_main(["--to", "it", "-t", "Hello"],
                                    env={"GEMINI_API_KEY": FAKE_KEY})
        self.assertEqual(code, 1)
        self.assertNotIn(FAKE_KEY, err)
        self.assertIn("***", err)


if __name__ == "__main__":
    unittest.main()
