"""Unit tests of skill-maker/scripts/readme_lint.py."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skill-maker", "scripts")
sys.path.insert(0, SCRIPTS)

import readme_lint  # noqa: E402

HEAD = "---\nsummary: One line.\n---\n\n# demo\n\nIntro paragraph.\n\n"


SCENARIO = "### Scenario\n\n**Context:** A.\n\n**Action:** B.\n\n**Result:** C.\n"
TEMPLATES = os.path.join(SCRIPTS, "..", "skills", "skill-readme", "assets")


def section(title, body="Text.\n"):
    return "## %s\n\n%s\n" % (title, body)


def skill_readme(*titles):
    titles = titles or ("Why", "Use cases", "Usage", "Inputs and outputs")
    return HEAD + "".join(section(t, SCENARIO if t.lower() == "use cases" else "Text.\n") for t in titles)


def plugin_readme(*extra_before_license):
    core = ("Why", "Use cases", "Included components", "Installation", "Quick start")
    return skill_readme(*(core + extra_before_license + ("License",)))


def errors(findings):
    return [(f["section"], f["message"]) for f in findings if f["severity"] == "error"]


def inventory(skills=(), agents=(), commands=(), hooks=()):
    return {"skills": list(skills), "agents": list(agents), "commands": list(commands), "hooks": list(hooks)}


class SkillProfileTest(unittest.TestCase):
    def lint(self, text, profile="skill", inv=None):
        return readme_lint.lint_text(text, profile, "README.md", inv)

    def test_minimal_readme_passes_without_conditional_sections(self):
        self.assertEqual(self.lint(skill_readme()), [])

    def test_all_conditional_sections_in_order_pass(self):
        text = skill_readme("Why", "Use cases", "Installation", "Usage", "Inputs and outputs",
                            "Requirements", "Limitations")
        self.assertEqual(self.lint(text), [])

    def test_headings_in_fenced_examples_are_ignored(self):
        text = skill_readme() + "```markdown\n# other\n## Why\n## Zeta\n```\n"
        self.assertEqual(self.lint(text), [])

    def test_missing_frontmatter_summary_h1_and_intro(self):
        found = errors(self.lint("## Why\n\nText.\n"))
        self.assertIn(("frontmatter", "missing YAML frontmatter with `summary:`"), found)
        self.assertIn(("H1", "no H1 title"), found)
        found = errors(self.lint("---\nsummary:\n---\n# demo\n\n" + section("Why")))
        self.assertIn(("frontmatter", "`summary:` is missing or empty"), found)
        self.assertTrue(any(s == "introduction" for s, _ in found))

    def test_second_h1_is_an_error(self):
        self.assertIn("H1", [s for s, _ in errors(self.lint(skill_readme() + "# again\n"))])

    def test_missing_required_section(self):
        found = errors(self.lint(skill_readme("Why", "Use cases", "Usage")))
        self.assertEqual(found, [("Inputs and outputs", "required section is missing")])

    def test_out_of_order_section(self):
        found = errors(self.lint(skill_readme("Why", "Usage", "Use cases", "Inputs and outputs")))
        self.assertEqual([s for s, _ in found], ["Use cases"])
        self.assertIn("out of order", found[0][1])

    def test_duplicate_h2(self):
        found = errors(self.lint(skill_readme("Why", "Use cases", "Usage", "Usage", "Inputs and outputs")))
        self.assertTrue(any("duplicate H2" in m for _, m in found))

    def test_inexact_title_is_reported_once_not_as_missing(self):
        found = errors(self.lint(skill_readme("Why", "Use Cases", "Usage", "Inputs and outputs")))
        self.assertEqual(found, [("Use Cases", "title must be exactly `Use cases`")])

    def test_custom_sections_after_the_contract_are_notes(self):
        found = self.lint(skill_readme("Why", "Use cases", "Usage", "Inputs and outputs", "Options", "Performance"))
        self.assertEqual([(f["severity"], f["section"]) for f in found],
                         [("info", "Options"), ("info", "Performance")])

    def test_custom_section_inside_the_contract_is_an_error(self):
        found = errors(self.lint(skill_readme("Why", "Example", "Use cases", "Usage", "Inputs and outputs")))
        self.assertEqual(found, [("Example", "custom section must come after the contract sections")])

    def test_use_cases_needs_a_scenario_and_sections_need_text(self):
        text = HEAD + section("Why", "") + section("Use cases") + section("Usage") + section("Inputs and outputs")
        found = errors(self.lint(text))
        self.assertIn(("Why", "section is empty"), found)
        self.assertIn(("Use cases", "needs at least one scenario as an H3"), found)

    def test_scenario_parts_and_long_summary_are_warnings(self):
        text = skill_readme().replace("**Action:** B.\n\n", "").replace("One line.", "x" * 201)
        found = self.lint(text)
        self.assertEqual([(f["severity"], f["section"]) for f in found],
                         [("warning", "frontmatter"), ("warning", "Use cases")])
        self.assertIn("lacks **Action:**", found[1]["message"])

    def test_bundled_templates_follow_the_contract(self):
        for profile in ("plugin", "skill"):
            path = os.path.join(TEMPLATES, "%s-readme-template.md" % profile)
            self.assertEqual(readme_lint.lint_file(path, profile), [], path)

    def test_unknown_profile(self):
        with self.assertRaises(ValueError):
            self.lint(skill_readme(), profile="agent")


class PluginProfileTest(unittest.TestCase):
    def lint(self, text, inv=None):
        return readme_lint.lint_text(text, "plugin", "README.md", inv)

    def test_minimal_plugin_readme_passes(self):
        self.assertEqual(self.lint(plugin_readme()), [])

    def test_license_is_required_and_last(self):
        text = skill_readme("Why", "Use cases", "Included components", "Installation", "Quick start")
        self.assertEqual(errors(self.lint(text)), [("License", "required section is missing")])
        text = skill_readme("Why", "Use cases", "Included components", "Installation", "Quick start",
                            "License", "Development")
        self.assertIn(("License", "`License` must be the last section"), errors(self.lint(text)))

    def test_install_alias_is_an_inexact_title(self):
        text = skill_readme("Why", "Use cases", "Included components", "Install", "Quick start", "License")
        self.assertEqual(errors(self.lint(text)), [("Install", "title must be exactly `Installation`")])

    def test_custom_section_before_license_is_a_note(self):
        found = self.lint(plugin_readme("Uninstall"))
        self.assertEqual([(f["severity"], f["section"]) for f in found], [("info", "Uninstall")])

    def test_component_sections_follow_the_inventory(self):
        inv = inventory(agents=[{"name": "reviewer", "file": "agents/reviewer.md"}])
        found = errors(self.lint(plugin_readme(), inv))
        self.assertEqual([s for s, _ in found], ["Agents"])
        with_agents = skill_readme("Why", "Use cases", "Included components", "Agents", "Hooks",
                                   "Installation", "Quick start", "License")
        found = self.lint(with_agents, inv)
        self.assertEqual([(f["severity"], f["section"]) for f in found], [("warning", "Hooks")])

    def test_included_components_lists_and_links_every_skill(self):
        inv = inventory(skills=[
            {"name": "alpha", "readme": "skills/alpha/README.md", "readme_exists": True},
            {"name": "beta", "readme": "skills/beta/README.md", "readme_exists": False},
        ])
        found = self.lint(plugin_readme(), inv)
        self.assertEqual(errors(found), [("Included components", "distributed skill not listed: alpha"),
                                         ("Included components", "distributed skill not listed: beta")])


    def test_skill_name_inside_another_name_is_not_listed(self):
        inv = inventory(skills=[{"name": "voice", "readme": "skills/voice/README.md", "readme_exists": False},
                                {"name": "voice-write", "readme": "skills/voice-write/README.md",
                                 "readme_exists": False}])
        text = plugin_readme().replace("## Included components\n\nText.", "## Included components\n\n- `voice-write`")
        self.assertEqual(errors(self.lint(text, inv)),
                         [("Included components", "distributed skill not listed: voice")])


class FileAndCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def write(self, relative, text):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return path

    def test_relative_links_must_exist(self):
        self.write("references/a.md", "x")
        body = ("See [a](references/a.md#top), [b](missing.md), [c](https://example.com), [d](#usage) "
                "and `[e](in-code.md)`.\n")
        path = self.write("README.md", skill_readme().replace("Intro paragraph.", "Intro.") + body)
        found = errors(readme_lint.lint_file(path, "skill"))
        self.assertEqual(found, [("Inputs and outputs", "relative link target does not exist: missing.md")])

    def test_link_to_skill_readme_silences_the_warning(self):
        self.write("skills/alpha/README.md", "x")
        text = plugin_readme().replace("## Included components\n\nText.",
                                       "## Included components\n\n- [alpha](./skills/alpha/README.md)")
        path = self.write("README.md", text)
        inv = inventory(skills=[{"name": "alpha", "readme": "skills/alpha/README.md", "readme_exists": True}])
        self.assertEqual(readme_lint.lint_file(path, "plugin", inv), [])
        unlinked = self.write("README.md", text.replace("[alpha](./skills/alpha/README.md)", "alpha"))
        found = readme_lint.lint_file(unlinked, "plugin", inv)
        self.assertEqual([(f["severity"], f["message"]) for f in found],
                         [("warning", "no link to skills/alpha/README.md")])

    def test_draft_links_resolve_from_the_base_dir(self):
        self.write("plugin/skills/alpha/references/a.md", "x")
        draft = self.write("drafts/README.md", skill_readme() + "See [a](references/a.md).\n")
        self.assertEqual(len(errors(readme_lint.lint_file(draft, "skill"))), 1)
        target = os.path.join(self.root, "plugin", "skills", "alpha")
        self.assertEqual(readme_lint.lint_file(draft, "skill", base_dir=target), [])
        script = os.path.join(SCRIPTS, "readme_lint.py")
        done = subprocess.run([sys.executable, script, "--profile", "skill", "--base-dir", target, draft],
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_unreadable_file_is_an_error(self):
        found = readme_lint.lint_file(os.path.join(self.root, "nope.md"), "skill")
        self.assertEqual([f["section"] for f in found], ["file"])

    def test_cli_exit_status_and_json(self):
        script = os.path.join(SCRIPTS, "readme_lint.py")
        good = self.write("good/README.md", skill_readme())
        bad = self.write("bad/README.md", skill_readme("Why"))
        done = subprocess.run([sys.executable, script, "--profile", "skill", good], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("0 error(s)", done.stdout)
        done = subprocess.run([sys.executable, script, "--profile", "skill", "--json", bad],
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 1)
        self.assertEqual({f["path"] for f in json.loads(done.stdout)}, {bad})
        done = subprocess.run([sys.executable, script, "--profile", "plugin", "--plugin-root",
                               os.path.join(self.root, "nope"), good], capture_output=True, text=True)
        self.assertEqual(done.returncode, 2)


if __name__ == "__main__":
    unittest.main()
