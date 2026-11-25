"""Unit tests of skill-maker/scripts/skill_lint.py."""

import os
import sys
import tempfile
import unittest

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skill-maker", "scripts")
sys.path.insert(0, SCRIPTS)

import skill_lint  # noqa: E402

DESCRIPTION = "Checks things. Use when the user asks to check things. Not for other things."


class SkillLintTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = os.path.join(tmp.name, "alpha")
        os.makedirs(self.dir)
        self.skill(body="Run the check and report what you find.\n")

    def write(self, relative, text):
        path = os.path.join(self.dir, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def skill(self, body="", description=DESCRIPTION, extra=""):
        self.write("SKILL.md", "---\nname: alpha\ndescription: %s\n%s---\n\n# Alpha\n\n%s" % (description, extra, body))

    def found(self, portable=False, public=True):
        return [(f["severity"], f["section"]) for f in skill_lint.lint_skill(self.dir, portable, public)]

    def test_clean_skill_has_no_findings(self):
        self.assertEqual(self.found(), [])

    # S12 frontmatter keys
    def test_unknown_key_error_in_portable(self):
        self.skill(extra="colour: blue\n")
        self.assertIn(("error", "S12"), self.found(portable=True))

    def test_unknown_key_warning_in_plugin(self):
        self.skill(extra="colour: blue\n")
        self.assertEqual(self.found(portable=False), [("warning", "S12")])

    def test_cc_key_info_in_portable(self):
        self.skill(extra="argument-hint: \"<file>\"\n")
        self.assertEqual(self.found(portable=True), [("info", "S12")])

    def test_cc_key_fine_in_plugin(self):
        self.skill(extra="effort: high\n")
        self.assertEqual(self.found(portable=False), [])

    # S4 size
    def test_long_skill_warns(self):
        self.skill(body="Line.\n" * 501)
        self.assertEqual(self.found(), [("warning", "S4")])

    # P6 development files
    def test_dev_dirs_and_files_error(self):
        for relative in ("tests/a.md", "evals/evals.json", "alpha-workspace/x.md", "scenarios/s.md",
                         "scripts/test_a.py", "scripts/a_test.py"):
            self.write(relative, "x\n")
        self.assertEqual(self.found().count(("error", "P6")), 6)

    def test_ignored_artifacts_pass(self):
        self.write("scripts/__pycache__/a.cpython-313.pyc", "x")
        self.write(".DS_Store", "x")
        self.assertEqual(self.found(), [])

    # S7 script invocation
    def test_bare_script_in_code_block_warns(self):
        self.write("scripts/check.sh", "echo\n")
        self.skill(body="```bash\nscripts/check.sh --all\n```\n")
        self.assertEqual(self.found(), [("warning", "S7")])

    def test_run_inline_bare_script_warns(self):
        self.write("scripts/check.sh", "echo\n")
        self.skill(body="Re-run `scripts/check.sh` and compare.\n")
        self.assertEqual(self.found(), [("warning", "S7")])

    def test_bare_script_in_reference_warns(self):
        self.write("scripts/check.py", "pass\n")
        self.write("references/steps.md", "Then run `./scripts/check.py out`.\n")
        self.assertEqual(self.found(), [("warning", "S7")])

    def test_interpreter_call_passes(self):
        self.write("scripts/check.py", "pass\n")
        self.skill(body="```bash\npython3 scripts/check.py --all\n```\n\nRun `bash scripts/check.py`.\n")
        self.assertEqual(self.found(), [])

    def test_prose_mention_passes(self):
        self.write("scripts/check.py", "pass\n")
        self.skill(body="`scripts/check.py` writes the report.\n")
        self.assertEqual(self.found(), [])

    def test_unbundled_path_passes(self):
        self.skill(body="```text\nRun: scripts/sync.sh\n```\n\n```bash\nscripts/sync.sh\n```\n")
        self.assertEqual(self.found(), [])

    # P3 placeholders
    def test_placeholder_warns(self):
        self.skill(body="TODO: explain the second step.\n\nAsk {{user_name}} first.\n")
        self.assertEqual(self.found(), [("warning", "P3"), ("warning", "P3")])

    def test_placeholder_in_code_passes(self):
        self.skill(body="Flag `TODO` lines.\n\n```text\nTODO {{x}}\n```\n")
        self.assertEqual(self.found(), [])

    # S3 language
    def test_italian_trigger_warns(self):
        self.skill(description='Learns the voice. Use when the author says "non scrivo mai così" or '
                               '"fammi le domande difficili".')
        self.assertEqual(self.found(), [("warning", "S3"), ("warning", "S3")])

    def test_french_trigger_warns(self):
        self.skill(description='Writes text. Use for "rédige un message pour l\'équipe".')
        self.assertEqual(self.found(), [("warning", "S3")])

    def test_german_and_spanish_triggers_warn(self):
        self.skill(description='Writes text. Use for "schreib einen kurzen Bericht" or "escribe un post para LinkedIn".')
        self.assertEqual(self.found(), [("warning", "S3"), ("warning", "S3")])

    def test_loanwords_pass(self):
        self.skill(description='Makes images with "Nano Banana". Use for "kaizen" reviews, "ad hoc" fixes, '
                               '"per se" checks, a "résumé" or "make the sky purple". Not for "non-English" text.')
        self.assertEqual(self.found(), [])

    def test_foreign_in_code_fence_passes(self):
        self.skill(body='```text\n"non scrivo mai così"\nIl testo della mail non è pronto per il cliente.\n```\n')
        self.assertEqual(self.found(), [])

    def test_custom_skips_language(self):
        self.skill(description='Scrive. Usa quando l\'utente dice "non scrivo mai così".')
        self.assertEqual(self.found(public=False), [])

    def test_italian_body_warns(self):
        self.skill(body="Leggi il file e scrivi il riepilogo della sessione. Non cambiare i file che non sono "
                        "nel perimetro, e chiedi sempre prima di procedere con le modifiche della cartella.\n")
        self.assertEqual(self.found(), [("warning", "S3")])

    def test_english_body_passes(self):
        self.skill(body="Read the file and write the summary of the session. Do not change files outside the "
                        "scope, and always ask before you change the folder.\n")
        self.assertEqual(self.found(), [])

    # agents
    def test_agent_language_and_placeholder(self):
        path = os.path.join(self.dir, "agent.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write('---\nname: a\ndescription: Reviews. Use for "fammi le domande difficili".\n---\n\nTBD.\n')
        found = [(f["severity"], f["section"]) for f in skill_lint.lint_agent(path, True)]
        self.assertEqual(sorted(found), [("warning", "P3"), ("warning", "S3")])


if __name__ == "__main__":
    unittest.main()
