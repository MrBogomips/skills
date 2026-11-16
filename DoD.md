# Definition of Done

## Requirements

- [ ] Validator self-tests pass: `bash tests/selftest.sh`
- [ ] `marketplace.json` and `skills/` agree: `bash tests/validate.sh`
- [ ] Bundled-script tests pass: `python3 -m unittest discover -s tests -p 'test_*.py'`
- [ ] The codex-port block passes under dash: `CODEX_PORT_SH=dash python3 -m unittest discover -s tests -p 'test_codex_port_block.py'`
- [ ] The manifest schema is valid: `claude plugin validate . --strict`
- [ ] Every changed skill has its `version` bumped in `.claude-plugin/marketplace.json`
- [ ] The `README.md` skill list is updated when a skill is added, renamed or removed
- [ ] Skills follow the portability rules of `AGENTS.md`: frontmatter `name` equals the directory, bundled files by relative path, no personal paths, macOS/BSD-compatible scripts
- [ ] The pull request is merged into `main`, with the `validate` check green

## On Done

- After a merge that added or changed a skill, bring the local installs in line with the merged `main` without asking, from the repository root once `main` is pulled:
  1. **Touched skills**: the `skills/<name>/` directories in the merged pull request (`gh pr diff <n> --name-only`).
  2. **Harnesses in use**: those holding at least one skill of this repository at user level.
     - Claude Code: `claude plugin list` shows `<skill>@mrbogomips-skills` with scope user.
     - Codex: `~/.agents/skills/<skill>/` exists.
     - Antigravity: `~/.gemini/config/skills/<skill>/` exists.
  3. **Changed skill**: update it in every harness where it is installed.
     - Claude Code: `claude plugin marketplace update mrbogomips-skills`, then `claude plugin update <skill>@mrbogomips-skills`.
     - Codex, Antigravity: `DISABLE_TELEMETRY=1 npx -y skills add ./ -g -y --skill <skill> -a <agents>`, where `<agents>` lists `codex`, `antigravity` or both, only the ones where it is installed.
  4. **New skill**: install it in every harness in use: `claude plugin marketplace update mrbogomips-skills`, then `claude plugin install <skill>@mrbogomips-skills` (user scope), and the `npx skills add` command above with every agent in use.
  5. **Verify**: every copy matches the repository: `diff -rq -x __pycache__ skills/<skill> <dir>/<skill>` for `~/.agents/skills` and `~/.gemini/config/skills`. For Claude Code, `claude plugin list` shows the manifest `version`.
  6. **Report** what was updated or installed in each harness. Sessions that are already open pick it up only after a restart.
- Ask before acting when in doubt, for example:
  - a skill was renamed or removed: uninstalling the old name (`claude plugin uninstall <old>@mrbogomips-skills`, `npx skills remove -g <old>`) needs a yes;
  - a changed skill is missing from a harness in use: it may have been left out on purpose, so ask before installing it there;
  - a skill is installed at project scope, or from a source other than this repository (`npx skills list -g` shows the source);
  - the checkout is not at the merged `main`, or a harness's state cannot be read (command missing or failing).
