# skill-audit scenarios

## Fixture

A snapshot of this repository in a scratch git repository, so that any change shows in `git status`:

```bash
mkdir -p "$F" && git archive HEAD | tar -x -C "$F" && (cd "$F" && git init -q && git add -A && git commit -qm snapshot)
```

Run Claude Code from `$F` with the plugin loaded: `claude --plugin-dir <repo>/skill-maker`.

## Scenarios

- [scenario-verdicts.md](scenario-verdicts.md): every skill gets one verdict and nothing changes.
