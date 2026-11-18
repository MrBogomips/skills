# Definition of Done

## Requirements

- [ ] Validator self-tests pass: `bash tests/selftest.sh`
- [ ] Every `plugin.json` and its `skills/` agree: `bash tests/validate.sh`
- [ ] The kaizen Stop hook test passes: `bash tests/test-kaizen-stop-gate.sh`
- [ ] Bundled-script tests pass: `python3 -m unittest discover -s tests -p 'test_*.py'`
- [ ] The codex-port block passes under dash: `CODEX_PORT_SH=dash python3 -m unittest discover -s tests -p 'test_codex_port_block.py'`
- [ ] The manifest schemas are valid: `claude plugin validate . --strict`, and `claude plugin validate ./<plugin> --strict` for each plugin folder
- [ ] A pull request that changes a skill bumps `version` in the `plugin.json` of the plugin that ships it: `.claude-plugin/plugin.json` for `skills/`, `<plugin>/.claude-plugin/plugin.json` for a plugin folder (see `AGENTS.md` for patch, minor or major)
- [ ] The `README.md` skill and plugin lists are updated when a skill or plugin is added, renamed or removed, and each plugin README still says correctly whether its skills install alone
- [ ] Skills in `skills/` follow the portability rules of `AGENTS.md`: frontmatter `name` equals the directory, bundled files by relative path, no personal paths, macOS/BSD-compatible scripts; plugin folders follow its Plugins section
- [ ] A pull request that adds or changes a skill has had its description and its context use reviewed with the `skill-creator` skill: the description is short and keeps every trigger phrase, and the body and its references load only what a run needs. The review changes no behavior and runs no evals. The pull request description says what was reviewed and what changed
- [ ] The pull request is merged into `main`, with the `validate` check green

## On Done

- After a merge that added or changed a skill, bring the local installs in line with the merged `main` without asking, from the repository root once `main` is pulled:
  1. **Touched skills**: the `skills/<name>/` directories in the merged pull request (`gh pr diff <n> --name-only`). A touched plugin folder `<plugin>/` counts as a change to that plugin.
  2. **Harnesses in use**: those holding at least one skill of this repository at user level.
     - Claude Code: `claude plugin list` shows `skills@mrbogomips` (or, for a plugin folder, `<plugin>@mrbogomips`) with scope user.
     - Codex: `~/.agents/skills/<skill>/` exists.
     - Antigravity: `~/.gemini/config/skills/<skill>/` exists.
  3. **Changed skill**: update it in every harness where it is installed.
     - Claude Code: `claude plugin marketplace update mrbogomips`, then `claude plugin update skills@mrbogomips` (one plugin carries every skill in `skills/`) or `claude plugin update <plugin>@mrbogomips` for a plugin folder.
     - Codex, Antigravity: `DISABLE_TELEMETRY=1 npx -y skills add ./ -g -y --skill <skill> -a <agents>`, where `<agents>` lists `codex`, `antigravity` or both, only the ones where it is installed.
  4. **New skill**: Claude Code gets it with the plugin update of step 3; install it in the other harnesses in use with the `npx skills add` command above.
  5. **Verify**: every copy matches the repository: `diff -rq -x __pycache__ skills/<skill> <dir>/<skill>` for `~/.agents/skills` and `~/.gemini/config/skills`. For Claude Code, `claude plugin list` shows each updated plugin at the `version` in its `plugin.json`.
  6. **Report** what was updated or installed in each harness. Sessions that are already open pick it up only after a restart.
- Ask before acting when in doubt, for example:
  - a skill was renamed or removed: removing the old name from the `skills` CLI installs (`npx skills remove -g <old>`) needs a yes;
  - a changed skill is missing from a harness in use: it may have been left out on purpose, so ask before installing it there;
  - a skill is installed at project scope, or from a source other than this repository (`npx skills list -g` shows the source);
  - the checkout is not at the merged `main`, or a harness's state cannot be read (command missing or failing).
