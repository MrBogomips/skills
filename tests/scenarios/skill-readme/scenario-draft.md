# Scenario: Draft mode

## Case 1: plugin with an existing README
Invocation: `/skill-maker:skill-readme draft personal-voice <scratch>/drafts`
- [ ] `<scratch>/drafts/README.md` and one `skills/<name>/README.md` per skill exist, plus `review-notes.md`
- [ ] `python3 skill-maker/scripts/readme_lint.py --profile plugin <scratch>/drafts/README.md` reports no error other than relative links to plugin files
- [ ] The Installation section keeps the "plugin only" statement and the migration note of the existing README
- [ ] The existing custom sections (`Setup`, `What the stores hold`, `What to expect`) are kept, after the contract sections
- [ ] `Configuration` documents `store_dir`, as `plugin.json` declares it
- [ ] The notes mark each scenario observed or illustrative and list what moved
- [ ] No draft contains a placeholder in angle brackets, an attribution line or a session link
- [ ] The `git status` diff is empty

## Case 2: skill with custom and generated sections
Invocation: `/skill-maker:skill-readme draft <eng-artifacts>/skills/erd <scratch>/drafts-erd`
- [ ] The draft keeps `summary:`, and the introduction says the same thing
- [ ] `Options`, `Example` and `Performance` are kept after the contract sections; `Performance` is byte for byte the existing text
- [ ] The Why states the measured performance and points to the `Performance` section
- [ ] A reader finds the first invocation in `Usage` and can tell which file is produced and where
- [ ] `git status` in the eng-artifacts checkout is unchanged

## Case 3: applying a draft
After case 1, ask: "apply the draft of the plugin README".
- [ ] The skill asks how existing documents are to be updated before touching the file, unless the project instructions already say
- [ ] It shows the difference first, then runs `validate.py` and reports its output unchanged
- [ ] Discard the change afterwards: `git checkout -- personal-voice/README.md`
