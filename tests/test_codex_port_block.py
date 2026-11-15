"""Behaviour of skills/port-to-agents/templates/codex-port-block.sh with a stub npx (no network)."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

# CODEX_PORT_SH picks the shell, e.g. dash, to check the block stays POSIX.
SHELL = os.environ.get("CODEX_PORT_SH", "sh")
BLOCK = Path(__file__).resolve().parent.parent / "skills/port-to-agents/templates/codex-port-block.sh"

# Mirrors rulesync's layout (skills -> .agents/skills, agents -> .codex/agents/*.toml) and fails
# when a skill linked into .agents/skills reaches the conversion.
STUB_NPX = """#!/bin/sh
case "$*" in *--version*) echo 9.9.9; exit 0 ;; esac
for s in .claude/skills/*; do
  if [ -L "$s" ]; then echo "stub rulesync: linked skill $s reached the conversion" >&2; exit 1; fi
done
for s in .claude/skills/*/; do
  [ -d "$s" ] || continue
  n=$(basename "$s"); mkdir -p ".agents/skills/$n"; cp -R "$s". ".agents/skills/$n/"
done
"""

SHARED = ".agents/skills/openspec-propose/SKILL.md"
TEXT = "---\nname: openspec-propose\ndescription: Use when proposing.\n---\nPropose.\n"


class LinkedSkillTest(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix="codex-port-repo-")).resolve()
        self.bin = Path(tempfile.mkdtemp(prefix="codex-port-bin-"))
        (self.bin / "npx").write_text(STUB_NPX)
        (self.bin / "npx").chmod(0o755)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        self.write("AGENTS.md", "# Rules\n")
        os.symlink("AGENTS.md", self.repo / "CLAUDE.md")
        self.write(".claude/skills/alpha/SKILL.md", "---\nname: alpha\ndescription: A.\n---\nA.\n")
        self.write(SHARED, TEXT)
        os.symlink("../../.agents/skills/openspec-propose", self.repo / ".claude/skills/openspec-propose")

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)
        shutil.rmtree(self.bin, ignore_errors=True)

    def write(self, path, text):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def read(self, path):
        return (self.repo / path).read_text()

    def run_block(self, *args, **extra_env):
        env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}", **extra_env)
        cmd = f'. "{BLOCK}"; codex_port "$@"'
        result = subprocess.run([SHELL, "-c", cmd, "sh", *args], cwd=self.repo, env=env,
                                capture_output=True, text=True)
        return result.returncode, result.stdout + result.stderr

    def test_linked_skill_is_left_to_its_owner(self):
        code, out = self.run_block()
        self.assertEqual(code, 0, out)
        self.assertIn("wrote 1 skills and 0 agents", out)
        self.assertEqual(self.read(SHARED), TEXT)
        self.assertNotIn("openspec-propose", self.read(".codex/codex-port.manifest"))

    def test_check_passes_with_a_linked_skill(self):
        self.assertEqual(self.run_block()[0], 0)
        code, out = self.run_block("--check")
        self.assertEqual(code, 0, out)
        self.assertIn("(1 skills, 0 agents)", out)

    def test_older_manifest_listing_linked_files_does_not_delete_them(self):
        self.assertEqual(self.run_block()[0], 0)
        manifest = self.read(".codex/codex-port.manifest")
        self.write(".codex/codex-port.manifest", manifest + SHARED + "\n")
        code, out = self.run_block()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read(SHARED), TEXT)

    def test_absolute_link_into_agents_skills_counts_too(self):
        link = self.repo / ".claude/skills/openspec-propose"
        link.unlink()
        os.symlink(self.repo / ".agents/skills/openspec-propose", link)
        code, out = self.run_block()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read(SHARED), TEXT)

    def test_link_elsewhere_is_still_ported(self):
        self.write("elsewhere/gamma/SKILL.md", "---\nname: gamma\ndescription: G.\n---\nG.\n")
        os.symlink("../../elsewhere/gamma", self.repo / ".claude/skills/gamma")
        code, out = self.run_block("--dry-run")
        # The stub refuses every link; a personal link must still reach rulesync.
        self.assertNotEqual(code, 0, out)
        self.assertIn("linked skill .claude/skills/gamma reached the conversion", out)

    def test_check_fails_when_git_ignores_a_linked_skill(self):
        self.write(".gitignore", "/.agents/\n")
        self.assertEqual(self.run_block()[0], 0)
        code, out = self.run_block("--check")
        self.assertNotEqual(code, 0, out)
        self.assertIn("openspec-propose", out)

    def test_only_shared_skills_leave_nothing_to_convert(self):
        shutil.rmtree(self.repo / ".claude/skills/alpha")
        (self.bin / "npx").write_text("#!/bin/sh\necho 'stub npx: called' >&2; exit 1\n")
        code, out = self.run_block()
        self.assertEqual(code, 0, out)
        self.assertIn("nothing to convert", out)
        self.assertEqual(self.read(SHARED), TEXT)

    def test_generation_warns_when_git_ignores_a_linked_skill(self):
        self.write(".gitignore", "/.agents/\n")
        code, out = self.run_block()
        self.assertEqual(code, 0, out)
        self.assertIn("warning: .claude/skills/openspec-propose links to .agents/skills/openspec-propose", out)

    def test_check_fails_when_a_linked_skill_dangles(self):
        # A fresh clone where git ignored the owner's files: only the link arrived.
        self.write(".gitignore", "/.agents/\n")
        self.assertEqual(self.run_block()[0], 0)
        shutil.rmtree(self.repo / ".agents/skills/openspec-propose")
        code, out = self.run_block("--check")
        self.assertNotEqual(code, 0, out)
        self.assertIn(".claude/skills/openspec-propose", out)
        self.assertIn("missing", out)

    def test_cdpath_does_not_hide_a_linked_skill(self):
        code, out = self.run_block(CDPATH=".")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read(SHARED), TEXT)

    def test_link_named_apart_from_its_target_keeps_the_target_files(self):
        link = self.repo / ".claude/skills/openspec-propose"
        link.unlink()
        os.symlink("../../.agents/skills/openspec-propose", self.repo / ".claude/skills/propose")
        self.assertEqual(self.run_block()[0], 0)
        manifest = self.read(".codex/codex-port.manifest")
        self.write(".codex/codex-port.manifest", manifest + SHARED + "\n")
        code, out = self.run_block()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read(SHARED), TEXT)

    def test_generation_with_a_dangling_link_warns_and_keeps_it_from_rulesync(self):
        shutil.rmtree(self.repo / ".agents/skills/openspec-propose")
        code, out = self.run_block()
        self.assertEqual(code, 0, out)
        self.assertIn("warning: .claude/skills/openspec-propose links to", out)


if __name__ == "__main__":
    unittest.main()
