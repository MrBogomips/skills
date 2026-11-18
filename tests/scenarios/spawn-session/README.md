# spawn-session scenarios

Manual pilot of `spawn-session`, one run per environment: the Claude desktop app, Herdr, a terminal with
Claude Code background sessions, and the manual fallback. Each run needs a live master session.

## Fixture

A test hub with two fake repositories, each with a skill and an agent of its own, so a child can show that it
loaded its repository's setup:

```bash
H=$(mktemp -d)/hub
for r in frontend backend; do
  mkdir -p "$H/$r/.claude/skills/hello-$r" "$H/$r/.claude/agents"
  git -C "$H/$r" init -q -b main
  printf '# %s\n\nWork on feature branches.\n' "$r" > "$H/$r/AGENTS.md"
  ln -s AGENTS.md "$H/$r/CLAUDE.md"
  printf -- '---\nname: hello-%s\ndescription: Says hello from %s. Use when asked to say hello.\n---\n\nReply "hello from %s".\n' \
    "$r" "$r" "$r" > "$H/$r/.claude/skills/hello-$r/SKILL.md"
  printf -- '---\nname: %s-reviewer\ndescription: Reviews %s changes.\n---\n\nReview the diff.\n' \
    "$r" "$r" > "$H/$r/.claude/agents/$r-reviewer.md"
  git -C "$H/$r" add -A && git -C "$H/$r" commit -qm init
done
printf '# Hub\n\n## Confidentiality\n\nNever name the client in commits.\n' > "$H/AGENTS.md"
echo "$H"
```

Open the master session in `$H` with `spawn-session` installed.

## Scenario

See [scenario-pilot.md](scenario-pilot.md).
