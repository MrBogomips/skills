# Rules for structure

### P1. The name is the directory

A skill's `name` equals its directory name: lowercase words joined by hyphens, at most 64 characters.
Tools install a skill under its `name`, so a mismatch gives it two identities.

Official source: agentskills-spec · Checked by: validator

### P2. Paths stay inside the component

A skill refers to its own files by paths relative to its directory. A plugin-only skill may use
`${CLAUDE_PLUGIN_ROOT}`. A file a skill writes into a user's project never refers to the plugin's
location, which changes with every install.

Official source: docs-plugins-reference · Checked by: reviewer

### P3. No leftover placeholders

No `TODO`, `TBD`, `FIXME` or template tokens (`{{name}}`, `<placeholder>`) outside code. A placeholder in
a published skill is read as an instruction.

Checked by: validator

### P4. Nothing from the author's machine

No personal paths, internal identifiers or private project names. A published skill runs on other
people's machines.

Checked by: reviewer

### P5. The manifest identifies the version

A plugin manifest has `name`, a semantic `version` and a `description`. The version changes with every
release, because installed plugins update only when it does.

Official source: docs-plugins-reference · Checked by: validator

### P6. Development files do not ship

Inside a skill directory there are no `tests/`, `evals/`, `scenarios/` or `*-workspace/` folders and no
`test_*.py` or `*_test.py` files (rule T7). Build artifacts that version control ignores
(`__pycache__/`, `.DS_Store`) are not counted.

Checked by: validator
