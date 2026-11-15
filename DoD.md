# Definition of Done

## Definition of Done

- [ ] Validator self-tests pass: `bash tests/selftest.sh`
- [ ] `marketplace.json` and `skills/` agree: `bash tests/validate.sh`
- [ ] Bundled-script tests pass: `python3 -m unittest discover -s tests -p 'test_*.py'`
- [ ] The codex-port block passes under dash: `CODEX_PORT_SH=dash python3 -m unittest discover -s tests -p 'test_codex_port_block.py'`
- [ ] The manifest schema is valid: `claude plugin validate . --strict`
- [ ] Every changed skill has its `version` bumped in `.claude-plugin/marketplace.json`
- [ ] The `README.md` skill list is updated when a skill is added, renamed or removed
- [ ] Skills follow the portability rules of `CLAUDE.md`: frontmatter `name` equals the directory, bundled files by relative path, no personal paths, macOS/BSD-compatible scripts
- [ ] The pull request is merged into `main`, with the `validate` check green

## On Done

- After a merge that changed a skill, offer to update the local install: `claude plugin marketplace update mrbogomips-skills`, then `claude plugin update <skill>@mrbogomips-skills`.
