"""Offline tests for codex_image.py and google_image.py: no network, no codex, no API key.

Run from the repo root: python3 -m unittest discover -s tests -p 'test_*.py'
"""
import base64
import contextlib
import importlib.util
import io
import json
import os
import re
import stat
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

try:
    from PIL import Image
except ImportError:
    Image = None

ROOT = Path(__file__).resolve().parent.parent
CODEX_PATH = ROOT / "skills" / "codex-image-gen" / "scripts" / "codex_image.py"
GOOGLE_PATH = ROOT / "skills" / "google-image-gen" / "scripts" / "google_image.py"
FAKE_KEY = "AIzaSyFAKEFAKEFAKEFAKEFAKEFAKE0123456789"
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"0" * 32


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


codex = load("codex_image", CODEX_PATH)
google = load("google_image", GOOGLE_PATH)


def run_main(module, argv, env=None):
    """Run module.main(argv); return (exit code or None, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    code = None
    with mock.patch.dict(os.environ, env or {}, clear=False), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            module.main(argv)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


def png_bytes(size, color="red"):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def ok_response(raw=PNG, mime="image/png"):
    block = {"type": "image", "mime_type": mime, "data": base64.b64encode(raw).decode()}
    return {"steps": [{"type": "model_output", "content": [block]}]}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def http_error(code, message="boom"):
    body = io.BytesIO(json.dumps({"error": {"message": message}}).encode())
    return urllib.error.HTTPError("https://x", code, "reason", {}, body)


class SharedHelpersTest(unittest.TestCase):
    def test_shared_block_is_identical(self):
        marker = "# Shared helpers."
        blocks = []
        for path in (CODEX_PATH, GOOGLE_PATH):
            text = path.read_text(encoding="utf-8")
            start = text.rindex("# " + "-" * 10, 0, text.index(marker))
            end = text.index("# " + "-" * 10, text.index("def write_images"))
            blocks.append(text[start:end].strip())
        self.assertEqual(blocks[0], blocks[1])

    def both(self):
        return (codex, google)

    def test_output_paths_variants_and_extension(self):
        for mod in self.both():
            with self.subTest(mod=mod.__name__):
                self.assertEqual(mod.output_paths(Path("a/b.png"), ["png"]), [Path("a/b.png")])
                self.assertEqual(mod.output_paths(Path("b.png"), ["jpg"]), [Path("b.jpg")])
                self.assertEqual(mod.output_paths(Path("b.jpeg"), ["jpg"]), [Path("b.jpeg")])
                self.assertEqual(mod.output_paths(Path("b"), ["webp"]), [Path("b.webp")])
                self.assertEqual(mod.output_paths(Path("d/b.png"), ["png", "png", "jpg"]),
                                 [Path("d/b.png"), Path("d/b-2.png"), Path("d/b-3.jpg")])

    def test_sniff(self):
        for mod in self.both():
            self.assertEqual(mod.sniff(PNG), "png")
            self.assertEqual(mod.sniff(JPEG), "jpg")
            self.assertEqual(mod.sniff(b"RIFF1234WEBPxxxx"), "webp")
            self.assertIsNone(mod.sniff(b"nope"))
            self.assertEqual(mod.sniff(b"nope", "image/png"), "png")

    def test_parse_size_and_aspect(self):
        for mod in self.both():
            self.assertEqual(mod.parse_size("1080x1920"), (1080, 1920))
            self.assertEqual(mod.parse_size("64X32"), (64, 32))
            for bad in ("0x10", "10", "axb", "10x-5", "1080x"):
                with self.assertRaises(SystemExit):
                    with contextlib.redirect_stderr(io.StringIO()):
                        mod.parse_size(bad)
            self.assertEqual(mod.parse_aspect("16:9"), "16:9")
            for bad in ("16/9", "0:1", "wide", "16:"):
                with self.assertRaises(SystemExit):
                    with contextlib.redirect_stderr(io.StringIO()):
                        mod.parse_aspect(bad)

    @unittest.skipUnless(Image, "Pillow not installed")
    def test_fit_geometry(self):
        for mod in self.both():
            wide = png_bytes((200, 100), "red")
            for mode in ("pad", "crop"):
                out = Image.open(io.BytesIO(mod.fit_to_size(wide, (50, 100), mode)))
                self.assertEqual(out.size, (50, 100))
                self.assertEqual(out.format, "PNG")
            padded = Image.open(io.BytesIO(mod.fit_to_size(wide, (100, 100), "pad")))
            self.assertEqual(padded.getpixel((50, 2)), (0, 0, 0))       # black bar on top
            self.assertEqual(padded.getpixel((50, 50))[0], 255)         # image in the middle
            cropped = Image.open(io.BytesIO(mod.fit_to_size(wide, (100, 100), "crop")))
            self.assertEqual(cropped.getpixel((2, 2))[0], 255)          # no bars
            same = Image.open(io.BytesIO(mod.fit_to_size(wide, (400, 200), "pad")))
            self.assertEqual(same.size, (400, 200))

    def test_check_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            for mod in self.both():
                mod.check_output_dir(Path(tmp) / "new" / "deeper" / "x.png")   # creatable
                with self.assertRaises(SystemExit):
                    with contextlib.redirect_stderr(io.StringIO()):
                        mod.check_output_dir(Path(tmp))                         # is a directory

    def test_read_request_and_images(self):
        for mod in self.both():
            self.assertEqual(mod.read_request(" hi ", None), "hi")
            with contextlib.redirect_stderr(io.StringIO()):
                for args in ((None, None), ("  ", None), ("a", Path("b")), (None, Path("/no/such"))):
                    with self.assertRaises(SystemExit):
                        mod.read_request(*args)
                with self.assertRaises(SystemExit):
                    mod.check_images(Path("/no/such.png"), [])


class GoogleRequestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ref = Path(self.tmp.name) / "ref.png"
        self.ref.write_bytes(PNG)

    def test_plain_request(self):
        body = google.build_request("m", "a cat", [], edit=False, aspect=None)
        self.assertEqual(body, {"model": "m", "input": [{"type": "text", "text": "a cat"}]})

    def test_aspect_uses_native_field(self):
        body = google.build_request("m", "a cat", [], edit=False, aspect="16:9")
        self.assertEqual(body["response_format"], {"type": "image", "aspect_ratio": "16:9"})
        self.assertNotIn("16:9", body["input"][0]["text"])

    def test_edit_and_references(self):
        body = google.build_request("m", "make it blue", [self.ref, self.ref], edit=True, aspect=None)
        self.assertIn("edit target", body["input"][0]["text"])
        self.assertTrue(body["input"][0]["text"].endswith("make it blue"))
        self.assertEqual([p["type"] for p in body["input"]], ["text", "image", "image"])
        self.assertEqual(base64.b64decode(body["input"][1]["data"]), PNG)
        self.assertEqual(body["input"][1]["mime_type"], "image/png")
        refs = google.build_request("m", "a cat", [self.ref], edit=False, aspect=None)
        self.assertIn("visual reference", refs["input"][0]["text"])

    def test_non_image_reference_rejected(self):
        bad = Path(self.tmp.name) / "x.png"
        bad.write_bytes(b"not an image")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            google.image_part(bad)

    def test_model_default_and_env_override(self):
        env = {"GOOGLE_IMAGE_MODEL": ""}
        code, out, _ = run_main(google, ["-p", "x", "-o", "o.png", "--print-prompt"], env)
        self.assertIn(google.DEFAULT_MODEL, out)
        with mock.patch.dict(os.environ, {"GOOGLE_IMAGE_MODEL": "env-model"}):
            args = google.parse_args(["-p", "x", "-o", "o.png"])
            self.assertEqual(args.model, "env-model")
            args = google.parse_args(["-p", "x", "-o", "o.png", "--model", "cli-model"])
            self.assertEqual(args.model, "cli-model")


class GoogleKeyTest(unittest.TestCase):
    def clean_env(self, **extra):
        env = {k: "" for k in google.KEY_VARS}
        env.update(extra)
        return env

    def test_lookup_order(self):
        with mock.patch.dict(os.environ, self.clean_env(GEMINI_API_KEY="g1", GOOGLE_API_KEY="g2")):
            self.assertEqual(google.api_key(), "g1")
        with mock.patch.dict(os.environ, self.clean_env(GOOGLE_API_KEY="g2")):
            self.assertEqual(google.api_key(), "g2")

    def test_missing_key_exits_2_with_one_line(self):
        code, _, err = run_main(google, ["-p", "x", "-o", "o.png"], self.clean_env())
        self.assertEqual(code, 2)
        self.assertEqual(len(err.strip().splitlines()), 1)
        self.assertIn("GEMINI_API_KEY", err)

    def test_key_never_in_print_prompt(self):
        code, out, err = run_main(google, ["-p", "x", "-o", "o.png", "--print-prompt"],
                                  self.clean_env(GEMINI_API_KEY=FAKE_KEY))
        self.assertIsNone(code)
        self.assertNotIn(FAKE_KEY, out + err)
        self.assertNotIn("AIza", out + err)

    def test_scrub(self):
        self.assertNotIn(FAKE_KEY, google.scrub(f"bad key {FAKE_KEY} here"))
        self.assertNotIn("sekret", google.scrub("key sekret leaked", "sekret"))


class GoogleApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "o.png"
        self.env = {"GEMINI_API_KEY": FAKE_KEY, "GOOGLE_API_KEY": ""}

    def run_with(self, side_effect, extra=()):
        with mock.patch("urllib.request.urlopen", side_effect=side_effect) as urlopen:
            result = run_main(google, ["-p", "x", "-o", str(self.out), *extra], self.env)
        return result, urlopen

    def test_success_extension_follows_mime(self):
        (code, out, _), urlopen = self.run_with([FakeResponse(ok_response(JPEG, "image/jpeg"))])
        self.assertIsNone(code)
        self.assertTrue(self.out.with_suffix(".jpg").exists())
        self.assertFalse(self.out.exists())
        req = urlopen.call_args[0][0]
        self.assertEqual(req.get_header("X-goog-api-key"), FAKE_KEY)
        self.assertNotIn(FAKE_KEY, req.full_url)

    def test_variants_make_one_call_each(self):
        responses = [FakeResponse(ok_response()), FakeResponse(ok_response())]
        (code, _, _), urlopen = self.run_with(responses, ["-n", "2"])
        self.assertIsNone(code)
        self.assertEqual(urlopen.call_count, 2)
        self.assertTrue(self.out.exists() and self.out.with_name("o-2.png").exists())

    def test_http_errors_map_to_one_line_and_write_nothing(self):
        expected = {400: "HTTP 400", 401: "HTTP 401", 403: "HTTP 403", 429: "HTTP 429"}
        for status, text in expected.items():
            with self.subTest(status=status):
                (code, _, err), urlopen = self.run_with(
                    [http_error(status, f"bad key {FAKE_KEY}")])
                self.assertEqual(code, 1)
                self.assertIn(text, err)
                self.assertEqual(len(err.strip().splitlines()), 1)
                self.assertNotIn(FAKE_KEY, err)
                self.assertEqual(urlopen.call_count, 1)        # no retry
                self.assertFalse(self.out.exists())

    def test_5xx_retried_once_then_reported(self):
        (code, _, err), urlopen = self.run_with([http_error(503), http_error(503)])
        self.assertEqual(code, 1)
        self.assertIn("HTTP 503", err)
        self.assertEqual(urlopen.call_count, 2)

    def test_5xx_then_success(self):
        (code, _, _), urlopen = self.run_with([http_error(500), FakeResponse(ok_response())])
        self.assertIsNone(code)
        self.assertTrue(self.out.exists())

    def test_timeout_retried_once(self):
        (code, _, err), urlopen = self.run_with([TimeoutError(), TimeoutError()])
        self.assertEqual(code, 1)
        self.assertIn("timed out", err)
        self.assertEqual(urlopen.call_count, 2)

    def test_network_error_scrubbed(self):
        exc = urllib.error.URLError(f"down {FAKE_KEY}")
        (code, _, err), _ = self.run_with([exc])
        self.assertEqual(code, 1)
        self.assertNotIn(FAKE_KEY, err)

    def test_text_only_reply_surfaced_and_nothing_written(self):
        reply = {"steps": [{"type": "model_output",
                            "content": [{"type": "text", "text": "I can't draw that"}]}]}
        (code, _, err), _ = self.run_with([FakeResponse(reply)])
        self.assertEqual(code, 1)
        self.assertIn("I can't draw that", err)
        self.assertFalse(self.out.exists())

    def test_empty_response_means_no_image(self):
        (code, _, err), _ = self.run_with([FakeResponse({"status": "failed"})])
        self.assertEqual(code, 1)
        self.assertIn("no image", err)
        self.assertFalse(self.out.exists())

    def test_invalid_inputs_fail_before_any_call(self):
        for extra in (["--aspect", "wide"], ["--fit", "10"], ["-n", "0"], ["--edit", "/no/such.png"]):
            with self.subTest(extra=extra):
                (code, _, _), urlopen = self.run_with([], extra)
                self.assertEqual(code, 1)
                urlopen.assert_not_called()

    def test_fit_without_pillow_fails_before_any_call(self):
        with mock.patch.dict(sys.modules, {"PIL": None}):
            (code, _, err), urlopen = self.run_with([], ["--fit", "10x10"])
        self.assertEqual(code, 1)
        self.assertIn("Pillow", err)
        urlopen.assert_not_called()


class CodexTest(unittest.TestCase):
    def test_prompt_assembly(self):
        plain = codex.build_prompt("a cat", edit=False, has_refs=False, aspect=None)
        self.assertIn("## Image to generate\na cat", plain)
        self.assertNotIn("aspect ratio", plain)
        edit = codex.build_prompt("make it blue", edit=True, has_refs=False, aspect="16:9", variants=3)
        self.assertIn("edit target", edit)
        self.assertIn("## Change to make\nmake it blue", edit)
        self.assertIn("16:9 aspect ratio", edit)
        self.assertIn("3 distinct variants", edit)
        refs = codex.build_prompt("a cat", edit=False, has_refs=True, aspect=None)
        self.assertIn("visual reference", refs)

    def test_print_prompt_runs_nothing(self):
        code, out, _ = run_main(codex, ["-p", "a cat", "-o", "o.png", "--print-prompt"],
                                {"CODEX_BIN": "/no/such/codex"})
        self.assertIsNone(code)
        self.assertIn("a cat", out)

    def test_missing_binary(self):
        code, _, err = run_main(codex, ["-p", "x", "-o", "/tmp/never.png"], {"CODEX_BIN": "/no/such/codex"})
        self.assertEqual(code, 1)
        self.assertIn("not found", err)


class CodexFakeBinaryTest(unittest.TestCase):
    """End-to-end against a stand-in `codex` shell script."""
    SESSION = "019a0000-0000-7000-8000-000000000001"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home"
        self.out = Path(self.tmp.name) / "o.jpg"
        self.fake = Path(self.tmp.name) / "codex"

    def install(self, exec_body, login_rc=0):
        script = f"""#!/bin/sh
if [ "$1" = login ]; then exit {login_rc}; fi
{exec_body}
"""
        self.fake.write_text(script)
        self.fake.chmod(self.fake.stat().st_mode | stat.S_IEXEC)
        return {"CODEX_BIN": str(self.fake), "CODEX_HOME": str(self.home)}

    def run_it(self, env, extra=()):
        return run_main(codex, ["-p", "a cat", "-o", str(self.out), *extra], env)

    def test_success_writes_with_real_extension(self):
        d = self.home / "generated_images" / self.SESSION
        env = self.install(f"echo 'session id: {self.SESSION}' >&2\nmkdir -p {d}\n"
                           f"printf '\\211PNG\\r\\n\\032\\n0000' > {d}/a.png")
        code, out, _ = self.run_it(env)
        self.assertIsNone(code)
        self.assertTrue(self.out.with_suffix(".png").exists())
        self.assertFalse(self.out.exists())
        self.assertIn("Wrote", out)

    def test_no_image_writes_nothing(self):
        env = self.install(f"echo 'session id: {self.SESSION}' >&2\necho 'here is a drawing in words'")
        code, _, err = self.run_it(env)
        self.assertEqual(code, 1)
        self.assertIn("no image", err)
        self.assertIn("drawing in words", err)
        self.assertFalse(self.out.with_suffix(".png").exists())

    def test_quota(self):
        env = self.install("echo 'You hit your usage limit' >&2\nexit 1")
        code, _, err = self.run_it(env)
        self.assertEqual(code, 1)
        self.assertIn("out of quota", err)

    def test_not_logged_in_checked_before_running(self):
        env = self.install("touch " + str(Path(self.tmp.name) / "ran"), login_rc=1)
        code, _, err = self.run_it(env)
        self.assertEqual(code, 1)
        self.assertIn("not logged in", err)
        self.assertFalse((Path(self.tmp.name) / "ran").exists())

    def test_timeout(self):
        env = self.install("sleep 5")
        code, _, err = self.run_it(env, ["--timeout", "1"])
        self.assertEqual(code, 1)
        self.assertIn("timed out", err)

    def test_missing_session_id(self):
        env = self.install("echo hello")
        code, _, err = self.run_it(env)
        self.assertEqual(code, 1)
        self.assertIn("session id", err)

    def test_fit_without_pillow_fails_before_running(self):
        env = self.install("touch " + str(Path(self.tmp.name) / "ran"))
        with mock.patch.dict(sys.modules, {"PIL": None}):
            code, _, err = self.run_it(env, ["--fit", "10x10"])
        self.assertEqual(code, 1)
        self.assertIn("Pillow", err)
        self.assertFalse((Path(self.tmp.name) / "ran").exists())


if __name__ == "__main__":
    unittest.main()
