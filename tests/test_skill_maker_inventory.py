"""Unit tests of skill-maker/scripts/inventory.py."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skill-maker", "scripts")
sys.path.insert(0, SCRIPTS)

import inventory  # noqa: E402


def write(root, relative, text=""):
    path = os.path.join(root, relative)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def skill(root, relative, name=None):
    name = name or os.path.basename(relative)
    write(root, os.path.join(relative, "SKILL.md"), "---\nname: %s\ndescription: d\n---\n" % name)


def manifest(root, **fields):
    data = {"name": "demo", "version": "1.2.3", "description": "A demo."}
    data.update(fields)
    write(root, ".claude-plugin/plugin.json", json.dumps(data))


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def test_lists_skills_and_readme_presence(self):
        manifest(self.root)
        skill(self.root, "skills/alpha")
        skill(self.root, "skills/beta", name="beta-renamed")
        write(self.root, "skills/alpha/README.md", "# alpha\n")
        write(self.root, "skills/not-a-skill/notes.md")
        result = inventory.build_inventory(self.root)
        self.assertEqual(result["plugin"]["name"], "demo")
        self.assertEqual(result["plugin"]["version"], "1.2.3")
        self.assertFalse(result["plugin"]["readme_exists"])
        self.assertEqual([(s["name"], s["directory"], s["readme_exists"]) for s in result["skills"]],
                         [("alpha", "skills/alpha", True), ("beta-renamed", "skills/beta", False)])

    def test_agents_commands_and_hooks(self):
        manifest(self.root)
        write(self.root, "agents/reviewer.md", "---\nname: reviewer\ndescription: d\n---\n")
        write(self.root, "agents/nested/AGENT.md", "---\ndescription: d\n---\n")
        write(self.root, "agents/CHANGELOG.md", "# changes\n")
        write(self.root, "agents/nested/references/notes.md", "notes\n")
        write(self.root, "agents/readme.md", "---\nname: x\n---\n")
        write(self.root, "commands/feedback.md", "body\n")
        write(self.root, "hooks/hooks.json", json.dumps({"hooks": {"Stop": [], "PreToolUse": []}}))
        result = inventory.build_inventory(self.root)
        self.assertEqual(sorted(a["name"] for a in result["agents"]), ["nested", "reviewer"])
        self.assertEqual(result["commands"], [{"name": "feedback", "file": "commands/feedback.md"}])
        self.assertEqual([h["event"] for h in result["hooks"]], ["PreToolUse", "Stop"])

    def test_manifest_hooks_merge_with_the_default_file(self):
        manifest(self.root, hooks=["./extra.json", "./missing.json"], agents=[])
        write(self.root, "agents/reviewer.md", "---\nname: reviewer\ndescription: d\n---\n")
        write(self.root, "hooks/hooks.json", json.dumps({"hooks": {"Stop": []}}))
        write(self.root, "extra.json", json.dumps({"hooks": {"PreToolUse": []}}))
        result = inventory.build_inventory(self.root)
        self.assertEqual([(h["event"], h["file"]) for h in result["hooks"]],
                         [("Stop", "hooks/hooks.json"), ("PreToolUse", "extra.json"), ("unreadable", "missing.json")])
        self.assertEqual(result["agents"], [])

    def test_inline_manifest_hooks(self):
        manifest(self.root, hooks={"hooks": {"SessionStart": []}})
        result = inventory.build_inventory(self.root)
        self.assertEqual(result["hooks"], [{"event": "SessionStart", "file": ".claude-plugin/plugin.json"}])

    def test_excludes_internal_skills_fixtures_and_nested_plugins(self):
        manifest(self.root)
        skill(self.root, "skills/alpha")
        skill(self.root, ".claude/skills/internal")
        skill(self.root, ".agents/skills/openspec-propose")
        skill(self.root, "tests/fixtures/doctor/skills/fake")
        skill(self.root, "evals/results/run/skills/copy")
        skill(self.root, "node_modules/pkg/skills/dep")
        write(self.root, "other/.claude-plugin/plugin.json", "{}")
        skill(self.root, "other/skills/theirs")
        result = inventory.build_inventory(self.root)
        self.assertEqual([s["name"] for s in result["skills"]], ["alpha"])
        reasons = {e["skill_file"]: e["reason"] for e in result["excluded"]}
        self.assertEqual(reasons, {
            ".claude/skills/internal/SKILL.md": "internal skill of the repository",
            ".agents/skills/openspec-propose/SKILL.md": "internal skill of the repository",
            "tests/fixtures/doctor/skills/fake/SKILL.md": "test fixture or example",
            "evals/results/run/skills/copy/SKILL.md": "test fixture or example",
            "other/skills/theirs/SKILL.md": "belongs to the plugin in other",
        })

    def test_plugin_in_a_subfolder_sees_only_its_own_skills(self):
        manifest(self.root)
        skill(self.root, "skills/root-skill")
        sub = os.path.join(self.root, "voice")
        manifest(sub, name="voice")
        skill(sub, "skills/voice-write")
        result = inventory.build_inventory(sub)
        self.assertEqual(result["plugin"]["name"], "voice")
        self.assertEqual([s["name"] for s in result["skills"]], ["voice-write"])
        self.assertEqual(result["excluded"], [])

    def test_manifest_skills_field_adds_to_the_default_folder(self):
        manifest(self.root, skills=["./custom", "./single", "./skills"])
        skill(self.root, "custom/one")
        skill(self.root, "single")
        skill(self.root, "skills/default")
        skill(self.root, "elsewhere/stray")
        result = inventory.build_inventory(self.root)
        self.assertEqual([s["directory"] for s in result["skills"]], ["skills/default", "custom/one", "single"])
        self.assertEqual(result["excluded"], [{"skill_file": "elsewhere/stray/SKILL.md",
                                               "reason": "outside the plugin's skill folders"}])

    def test_missing_or_broken_manifest_is_an_error(self):
        with self.assertRaises(inventory.InventoryError):
            inventory.build_inventory(self.root)
        write(self.root, ".claude-plugin/plugin.json", "{not json")
        with self.assertRaises(inventory.InventoryError):
            inventory.build_inventory(self.root)
        write(self.root, ".claude-plugin/plugin.json", "[]")
        with self.assertRaises(inventory.InventoryError):
            inventory.build_inventory(self.root)

    def test_cli_prints_json_and_fails_cleanly(self):
        manifest(self.root)
        skill(self.root, "skills/alpha")
        script = os.path.join(SCRIPTS, "inventory.py")
        done = subprocess.run([sys.executable, script, self.root], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["skills"][0]["name"], "alpha")
        bad = subprocess.run([sys.executable, script, os.path.join(self.root, "nope")],
                             capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertIn("inventory:", bad.stderr)


if __name__ == "__main__":
    unittest.main()
