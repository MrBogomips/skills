"""Unit tests of skill-maker/scripts/validate.py."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skill-maker", "scripts")
sys.path.insert(0, SCRIPTS)

import validate  # noqa: E402

HEAD = "---\nsummary: One line.\n---\n\n# %s\n\nIntro paragraph.\n\n"
SKILL_README = HEAD + ("## Why\n\nText.\n\n## Use cases\n\n### Scenario\n\n**Context:** A.\n\n**Action:** B.\n\n**Result:** C.\n\n"
                       "## Usage\n\nText.\n\n## Inputs and outputs\n\nText.\n")
PLUGIN_README = HEAD + ("## Why\n\nText.\n\n## Use cases\n\n### Scenario\n\n**Context:** A.\n\n**Action:** B.\n\n**Result:** C.\n\n"
                        "## Included components\n\n- [alpha](skills/alpha/README.md)\n\n"
                        "## Agents\n\n`reviewer` checks things.\n\n"
                        "## Installation\n\nText.\n\n## Quick start\n\nText.\n\n## License\n\nMIT\n")


class ValidateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)
        self.write(".claude-plugin/plugin.json",
                   json.dumps({"name": "demo", "version": "0.1.0", "description": "A demo."}))
        self.write("README.md", PLUGIN_README % "demo")
        self.write("skills/alpha/SKILL.md", "---\nname: alpha\ndescription: Does alpha.\n---\n")
        self.write("skills/alpha/README.md", SKILL_README % "alpha")
        self.write("agents/reviewer.md", "---\nname: reviewer\ndescription: Reviews.\n---\n")

    def write(self, relative, text):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def errors(self):
        found = validate.validate(self.root, run_claude=False)
        return [(os.path.relpath(f["path"], self.root), f["section"]) for f in found if f["severity"] == "error"]

    def test_complete_plugin_has_no_findings(self):
        self.assertEqual(validate.validate(self.root, run_claude=False), [])

    def test_manifest_fields(self):
        self.write(".claude-plugin/plugin.json", json.dumps({"name": "Demo_X", "version": "1.0"}))
        self.assertEqual(self.errors()[:3], [(".claude-plugin/plugin.json", "name"),
                                             (".claude-plugin/plugin.json", "version"),
                                             (".claude-plugin/plugin.json", "description")])

    def test_missing_manifest_is_one_error(self):
        os.remove(os.path.join(self.root, ".claude-plugin", "plugin.json"))
        found = validate.validate(self.root, run_claude=False)
        self.assertEqual([(f["severity"], f["section"]) for f in found], [("error", "manifest")])

    def test_skill_frontmatter(self):
        self.write("skills/alpha/SKILL.md", "---\nname: other\ndescription: %s\n---\n" % ("x" * 1025))
        found = [e for e in self.errors() if e[0] == "skills/alpha/SKILL.md"]
        self.assertEqual(found, [("skills/alpha/SKILL.md", "name"), ("skills/alpha/SKILL.md", "description")])
        self.write("skills/alpha/SKILL.md", "no frontmatter\n")
        self.assertEqual(self.errors(), [("skills/alpha/SKILL.md", "frontmatter")])

    def test_agent_frontmatter(self):
        self.write("agents/reviewer.md", "---\nname: reviewer\n---\n")
        self.assertEqual(self.errors(), [("agents/reviewer.md", "description")])

    def test_missing_and_broken_readmes(self):
        os.remove(os.path.join(self.root, "skills", "alpha", "README.md"))
        self.assertIn(("skills/alpha/README.md", "file"), self.errors())
        self.write("skills/alpha/README.md", (SKILL_README % "alpha").replace("## Usage", "## How"))
        self.assertIn(("skills/alpha/README.md", "Usage"), self.errors())

    def test_plugin_readme_is_checked_against_components(self):
        self.write("README.md", (PLUGIN_README % "demo").replace("## Agents\n\n`reviewer` checks things.\n\n", ""))
        self.assertEqual(self.errors(), [("README.md", "Agents")])

    def test_cli_exit_status(self):
        script = os.path.join(SCRIPTS, "validate.py")
        done = subprocess.run([sys.executable, script, "--no-claude", self.root], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.write("README.md", "# demo\n")
        done = subprocess.run([sys.executable, script, "--no-claude", "--json", self.root],
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 1)
        self.assertTrue(json.loads(done.stdout))

    def fake_claude(self, body):
        bin_dir = os.path.join(self.root, "fakebin")
        os.makedirs(bin_dir, exist_ok=True)
        path = os.path.join(bin_dir, "claude")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\n" + body)
        os.chmod(path, 0o755)
        saved = os.environ.get("PATH", "")
        os.environ["PATH"] = bin_dir + os.pathsep + saved
        self.addCleanup(os.environ.__setitem__, "PATH", saved)

    def claude_findings(self):
        found = validate.validate(self.root)
        return [(f["severity"], f["message"]) for f in found if f["section"] == "claude plugin validate"]

    def test_claude_step_passes_the_root_and_strict(self):
        self.fake_claude('[ "$1 $2 $4" = "plugin validate --strict" ] && [ -d "$3" ]\n')
        self.assertEqual(self.claude_findings(), [("info", "passed with --strict")])

    def test_claude_step_failure_is_an_error_with_its_output(self):
        self.fake_claude('printf "bad field \\377\\n"; exit 1\n')
        found = self.claude_findings()
        self.assertEqual(found[0][0], "error")
        self.assertIn("bad field", found[0][1])

    def test_claude_step_reports_when_the_cli_is_missing(self):
        saved = os.environ.get("PATH", "")
        os.environ["PATH"] = self.root
        self.addCleanup(os.environ.__setitem__, "PATH", saved)
        found = validate.validate(self.root)
        self.assertEqual([(f["severity"], f["section"]) for f in found], [("info", "claude plugin validate")])


if __name__ == "__main__":
    unittest.main()
