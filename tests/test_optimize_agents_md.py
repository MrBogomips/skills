"""Offline tests for skills/optimize-agents-md/scripts/inventory.sh on temporary repositories.

Run from the repo root: python3 -m unittest discover -s tests -p 'test_*.py'
"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "optimize-agents-md" / "scripts" / "inventory.sh"
BASH = "/bin/bash" if os.path.exists("/bin/bash") else shutil.which("bash")


def lines_of(n, prefix="- line"):
    return "".join(f"{prefix} {i}\n" for i in range(n))


class InventoryCase(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix="oam-")).resolve()
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)

    def git_init(self):
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def write(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def link(self, rel, target):
        os.symlink(target, self.repo / rel)

    def run_inventory(self, *args, expect=0):
        proc = subprocess.run([BASH, str(SCRIPT), *args], capture_output=True, text=True)
        self.assertEqual(proc.returncode, expect, proc.stdout + proc.stderr)
        return proc.stdout

    def inventory(self):
        return self.run_inventory(str(self.repo)).splitlines()

    def value(self, out, key):
        found = [line.split(": ", 1)[1] for line in out if line.startswith(key + ": ")]
        self.assertEqual(len(found), 1, f"{key} in {out}")
        return found[0]

    def values(self, out, key):
        return [line.split(": ", 1)[1] for line in out if line.startswith(key + ": ")]

    def startup(self, out, harness):
        for v in self.values(out, "startup"):
            name, lines, size = v.split()
            if name == harness:
                return int(lines.split("=")[1]), int(size.split("=")[1])
        self.fail(f"no startup for {harness}: {out}")


class LayoutTests(InventoryCase):
    def test_claude_only(self):
        self.git_init()
        self.write("CLAUDE.md", lines_of(10))
        out = self.inventory()
        self.assertEqual(self.value(out, "layout"), "claude-only")
        self.assertEqual(self.value(out, "git"), "yes")
        self.assertIn("claude", self.value(out, "signals").split())
        self.assertEqual(self.startup(out, "claude")[0], 10)
        self.assertEqual(self.startup(out, "codex"), (0, 0))

    def test_symlink_pair_counts_the_shared_file_for_both(self):
        self.write("AGENTS.md", lines_of(7))
        self.link("CLAUDE.md", "AGENTS.md")
        out = self.inventory()
        self.assertEqual(self.value(out, "layout"), "symlink")
        self.assertIn("CLAUDE.md link=AGENTS.md", self.values(out, "file"))
        self.assertEqual(self.startup(out, "claude"), self.startup(out, "codex"))
        self.assertEqual(self.startup(out, "codex")[0], 7)
        self.assertEqual(self.value(out, "git"), "no")

    def test_symlink_written_with_a_dot_slash_is_still_a_symlink(self):
        self.write("AGENTS.md", lines_of(2))
        self.link("CLAUDE.md", "./AGENTS.md")
        self.assertEqual(self.value(self.inventory(), "layout"), "symlink")

    def test_reverse_symlink(self):
        self.write("CLAUDE.md", lines_of(3))
        self.link("AGENTS.md", "CLAUDE.md")
        self.assertEqual(self.value(self.inventory(), "layout"), "symlink-reverse")

    def test_regular_pair_drifted_and_identical(self):
        self.write("CLAUDE.md", lines_of(3))
        self.write("AGENTS.md", lines_of(4))
        self.assertEqual(self.value(self.inventory(), "layout"), "pair-drifted")
        self.write("AGENTS.md", lines_of(3))
        self.assertEqual(self.value(self.inventory(), "layout"), "pair-identical")

    def test_import_layout_and_imported_bytes_count_at_start(self):
        self.write("AGENTS.md", lines_of(5))
        self.write("CLAUDE.md", "@AGENTS.md\n- claude only\n")
        out = self.inventory()
        self.assertEqual(self.value(out, "layout"), "import")
        self.assertIn("CLAUDE.md @AGENTS.md", self.values(out, "import"))
        claude_md = (self.repo / "CLAUDE.md").stat().st_size
        agents_md = (self.repo / "AGENTS.md").stat().st_size
        self.assertEqual(self.startup(out, "claude"), (7, claude_md + agents_md))

    def test_a_file_imported_twice_or_already_loaded_counts_once(self):
        self.write("CLAUDE.md", "- main\n")
        self.write(".claude/CLAUDE.md", "@../CLAUDE.md\n@../docs/x.md\n@../docs/x.md\n")
        self.write("docs/x.md", lines_of(3))
        self.assertEqual(self.startup(self.inventory(), "claude")[0], 1 + 3 + 3)

    def test_agents_only_is_read_by_claude_fallback(self):
        self.write("AGENTS.md", lines_of(4))
        out = self.inventory()
        self.assertEqual(self.value(out, "layout"), "agents-only")
        self.assertEqual(self.startup(out, "claude")[0], 4)

    def test_no_instruction_file(self):
        out = self.inventory()
        self.assertEqual(self.value(out, "layout"), "none")
        self.assertEqual(self.startup(out, "claude"), (0, 0))


class StartupTests(InventoryCase):
    def test_unscoped_rules_load_at_start_scoped_rules_do_not(self):
        self.write("CLAUDE.md", lines_of(2))
        self.write(".claude/rules/always.md", lines_of(3))
        self.write(".claude/rules/web.md", '---\npaths:\n  - "web/**"\n---\n' + lines_of(20))
        out = self.inventory()
        self.assertEqual(self.startup(out, "claude")[0], 5)
        rules = self.values(out, "rule")
        self.assertTrue(any(r.startswith(".claude/rules/always.md unscoped") for r in rules), rules)
        self.assertTrue(any(r.startswith(".claude/rules/web.md scoped") for r in rules), rules)

    def test_rule_with_a_space_in_its_name_is_counted(self):
        self.write("CLAUDE.md", lines_of(1))
        self.write(".claude/rules/my rule.md", lines_of(3))
        out = self.inventory()
        self.assertTrue(any(r.startswith(".claude/rules/my rule.md unscoped lines=3") for r in self.values(out, "rule")), out)
        self.assertEqual(self.startup(out, "claude")[0], 4)

    def test_symlinked_rule_is_counted(self):
        self.write("CLAUDE.md", lines_of(1))
        self.write("shared/r.md", lines_of(3))
        (self.repo / ".claude/rules").mkdir(parents=True)
        os.symlink("../../shared/r.md", self.repo / ".claude/rules/r.md")
        self.assertEqual(self.startup(self.inventory(), "claude")[0], 4)

    def test_dot_claude_and_local_files_load_for_claude_only(self):
        self.write("AGENTS.md", lines_of(2))
        self.link("CLAUDE.md", "AGENTS.md")
        self.write(".claude/CLAUDE.md", lines_of(3))
        self.write("CLAUDE.local.md", lines_of(1))
        out = self.inventory()
        self.assertEqual(self.startup(out, "claude")[0], 6)
        self.assertEqual(self.startup(out, "codex")[0], 2)

    def test_agents_override_replaces_agents_for_codex(self):
        self.write("AGENTS.md", lines_of(9))
        self.write("AGENTS.override.md", lines_of(2))
        self.assertEqual(self.startup(self.inventory(), "codex")[0], 2)

    def test_nested_files_are_listed_but_not_loaded_at_start(self):
        self.write("CLAUDE.md", lines_of(2))
        self.write("web/CLAUDE.md", lines_of(30))
        self.write("api/AGENTS.md", lines_of(4))
        self.write("node_modules/pkg/CLAUDE.md", lines_of(1))
        out = self.inventory()
        nested = self.values(out, "nested")
        self.assertTrue(any(n.startswith("web/CLAUDE.md ") for n in nested), nested)
        self.assertTrue(any(n.startswith("api/AGENTS.md ") for n in nested), nested)
        self.assertFalse(any("node_modules" in n for n in nested), nested)
        self.assertEqual(self.startup(out, "claude")[0], 2)

    def test_worktrees_inside_the_repo_are_not_nested_files(self):
        self.write("CLAUDE.md", lines_of(1))
        self.write(".claude/worktrees/feat/CLAUDE.md", lines_of(1))
        self.write(".worktrees/fix/AGENTS.md", lines_of(1))
        self.write("other-checkout/.git", "gitdir: /elsewhere\n")
        self.write("other-checkout/CLAUDE.md", lines_of(1))
        self.assertEqual(self.values(self.inventory(), "nested"), [])

    def test_a_missing_import_target_is_not_counted(self):
        self.write("CLAUDE.md", "Contact @anthropic-ai or see @docs/none.md\n")
        out = self.inventory()
        self.assertEqual(self.values(out, "import"), [])
        self.assertEqual(self.startup(out, "claude")[0], 1)


class WarningAndSignalTests(InventoryCase):
    def test_warns_over_200_lines(self):
        self.write("CLAUDE.md", lines_of(201))
        warns = self.values(self.inventory(), "warn")
        self.assertTrue(any("CLAUDE.md" in w and "200" in w for w in warns), warns)

    def test_no_warning_at_200_lines(self):
        self.write("CLAUDE.md", lines_of(200))
        self.assertEqual(self.values(self.inventory(), "warn"), [])

    def test_warns_when_codex_start_exceeds_32_kib(self):
        self.write("AGENTS.md", "x" * 40000 + "\n")
        warns = self.values(self.inventory(), "warn")
        self.assertTrue(any("codex" in w and "32768" in w for w in warns), warns)

    def test_signals(self):
        self.write("CLAUDE.md", "x\n")
        (self.repo / ".codex").mkdir()
        self.write("GEMINI.md", "x\n")
        (self.repo / ".cursor").mkdir()
        self.write(".github/copilot-instructions.md", "x\n")
        signals = self.value(self.inventory(), "signals").split()
        for s in ("claude", "codex", "gemini", "cursor", "copilot"):
            self.assertIn(s, signals)

    def test_skills_are_listed_with_their_scope(self):
        self.write("CLAUDE.md", "x\n")
        self.write(".claude/skills/release/SKILL.md", "---\nname: release\n---\n")
        self.write(".agents/skills/lint/SKILL.md", "---\nname: lint\n---\n")
        self.write("skills/tool/SKILL.md", "---\nname: tool\n---\n")
        out = self.inventory()
        self.assertIn(".claude/skills/release/SKILL.md", self.values(out, "skill"))
        self.assertIn(".agents/skills/lint/SKILL.md", self.values(out, "skill"))
        self.assertIn("skills/tool/SKILL.md", self.values(out, "skill-candidate"))


class ErrorTests(InventoryCase):
    def test_missing_root_is_an_error(self):
        self.run_inventory(str(self.repo / "nope"), expect=2)

    def test_defaults_to_current_directory(self):
        self.write("CLAUDE.md", lines_of(4))
        proc = subprocess.run([BASH, str(SCRIPT)], capture_output=True, text=True, cwd=self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("layout: claude-only", proc.stdout)


if __name__ == "__main__":
    unittest.main()
