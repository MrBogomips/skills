# >>> codex-port >>>
# Managed by the codex-port skill; a later run replaces this block. AGENTS.md is the shared
# instruction file, written by hand; CLAUDE.md is a symlink to it, and Claude Code's own lines
# live in .claude/CLAUDE.md. This block never writes them. Edit the Claude Code sources
# (.claude/, .mcp.json), never the generated Codex files.
#
# codex_port [--dry-run | --check] [--force]
#   Checks the instruction files (CLAUDE.md links to AGENTS.md; AGENTS.md holds no @import,
#   which Codex does not resolve), then regenerates the Codex files (.agents/skills/, .codex/)
#   from .claude/ and .mcp.json with the latest rulesync. It converts a copy of the sources in
#   a temporary folder and checks the result there, so a failed or surprising conversion leaves
#   the files as they were. It records what it wrote in .codex/codex-port.manifest and removes
#   what an earlier run wrote for a source that is gone.
#   --dry-run  list what it would write; change nothing
#   --check    check the files against the sources, without the network: the instruction
#              files, and every skill and agent has its Codex file
#   --force    overwrite a file of the same name that codex-port did not write
#   Call it as a plain command, never as `codex_port || ...`, which turns off its error checks.
codex_port() (
  set -eu
  cp_dry=0 cp_check=0 cp_force=0
  for cp_arg in "$@"; do
    case $cp_arg in
      --dry-run) cp_dry=1 ;;
      --check) cp_check=1 ;;
      --force) cp_force=1 ;;
      *) echo "codex-port: unknown option '$cp_arg'" >&2; return 2 ;;
    esac
  done
  cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  cp_manifest=.codex/codex-port.manifest
  cp_version=
  if [ -L .agents ] || [ -L .codex ]; then
    echo "codex-port: .agents or .codex is a symbolic link; it writes through neither" >&2
    return 1
  fi

  # cp_instructions: AGENTS.md is the real file, CLAUDE.md a symlink to it.
  cp_instructions() {
    cp_fail=0
    if [ ! -e AGENTS.md ] && [ ! -e CLAUDE.md ] && [ ! -L CLAUDE.md ] && [ ! -e .claude/CLAUDE.md ]; then return 0; fi
    if [ -L AGENTS.md ]; then
      echo "codex-port: AGENTS.md is a symlink: it must be the real file, and CLAUDE.md the link to it" >&2
      return 1
    fi
    if [ ! -f AGENTS.md ]; then
      echo "codex-port: AGENTS.md is missing: git mv CLAUDE.md AGENTS.md, move Claude Code's own lines to .claude/CLAUDE.md, then ln -s AGENTS.md CLAUDE.md" >&2
      return 1
    fi
    if head -n 1 AGENTS.md | grep -qF '<!-- Generated from CLAUDE.md by codex-port'; then
      echo "codex-port: AGENTS.md is the output of an earlier codex-port: make it the shared file" >&2
      return 1
    fi
    if [ -L CLAUDE.md ]; then
      if [ "$(readlink CLAUDE.md)" != AGENTS.md ]; then
        echo "codex-port: CLAUDE.md links to '$(readlink CLAUDE.md)', not to AGENTS.md: ln -sf AGENTS.md CLAUDE.md" >&2; cp_fail=1
      fi
    elif [ -f CLAUDE.md ] && [ "$(cat CLAUDE.md)" = AGENTS.md ]; then
      echo "codex-port: CLAUDE.md is a symlink checked out as a text file: turn on core.symlinks (Windows: Developer Mode) and check it out again" >&2; cp_fail=1
    elif [ -f CLAUDE.md ]; then
      echo "codex-port: CLAUDE.md is a regular file: move Claude Code's own lines to .claude/CLAUDE.md, the rest to AGENTS.md, then ln -sf AGENTS.md CLAUDE.md" >&2; cp_fail=1
    else
      echo "codex-port: CLAUDE.md is missing: ln -s AGENTS.md CLAUDE.md" >&2; cp_fail=1
    fi
    if [ -f .claude/CLAUDE.md ] && grep -qE '^@(\.\./)?AGENTS\.md[[:space:]]*$' .claude/CLAUDE.md; then
      echo "codex-port: .claude/CLAUDE.md imports AGENTS.md, which CLAUDE.md already is: remove the import" >&2; cp_fail=1
    fi
    if grep -q '^@[^[:space:]]' AGENTS.md; then
      echo "codex-port: AGENTS.md has an @import line, which Codex does not resolve: inline it" >&2; cp_fail=1
    fi
    if [ "$(wc -c <AGENTS.md)" -gt 32768 ]; then
      echo "codex-port: warning: AGENTS.md is over 32 KiB, Codex's default project_doc_max_bytes" >&2
    fi
    return $cp_fail
  }

  # cp_outputs <root>: the Codex files under <root> cover every skill and agent of this project.
  cp_outputs() {
    cp_fail=0 cp_skills=0 cp_agents=0
    for cp_src in .claude/skills/*/SKILL.md; do
      [ -f "$cp_src" ] || continue
      cp_name=$(basename "$(dirname "$cp_src")")
      cp_skills=$((cp_skills + 1))
      [ -f "$1/.agents/skills/$cp_name/SKILL.md" ] ||
        { echo "codex-port: skill '$cp_name' is not ported" >&2; cp_fail=1; }
    done
    for cp_src in .claude/agents/*.md; do
      [ -f "$cp_src" ] || continue
      cp_name=$(basename "$cp_src" .md)
      cp_agents=$((cp_agents + 1))
      [ -f "$1/.codex/agents/$cp_name.toml" ] ||
        { echo "codex-port: agent '$cp_name' is not ported" >&2; cp_fail=1; }
    done
    return $cp_fail
  }

  if [ "$cp_check" = 1 ]; then
    cp_bad=0
    cp_instructions || cp_bad=1
    cp_outputs . || cp_bad=1
    if [ "$cp_bad" = 1 ]; then return 1; fi
    echo "codex-port: the instruction files and the Codex files are up to date ($cp_skills skills, $cp_agents agents)"
    return 0
  fi
  cp_instructions

  # Only the features the sources have: rulesync writes a Codex approval policy into
  # .codex/config.toml for permissions it was never given. Never `rules`: it would overwrite
  # AGENTS.md with a copy of CLAUDE.md.
  cp_features=
  cp_feature() { cp_features=${cp_features:+$cp_features,}$1; }
  if ls .claude/skills/*/SKILL.md >/dev/null 2>&1; then cp_feature skills; fi
  if ls .claude/agents/*.md >/dev/null 2>&1; then cp_feature subagents; fi
  if [ -f .mcp.json ]; then cp_feature mcp; fi
  if grep -qs '"hooks"' .claude/settings.json; then cp_feature hooks; fi
  if grep -qs '"permissions"' .claude/settings.json; then cp_feature permissions; fi

  cp_list=
  if [ -n "$cp_features" ]; then
    # Convert a copy of the sources: personal files and harness worktrees stay out.
    cp_tmp=$(mktemp -d "${TMPDIR:-/tmp}/codex-port.XXXXXX")
    trap 'rm -rf "$cp_tmp"' EXIT
    if [ -f .mcp.json ]; then cp .mcp.json "$cp_tmp/"; fi
    if [ -d .claude ]; then
      mkdir "$cp_tmp/.claude"
      for cp_src in .claude/* .claude/.[!.]*; do
        [ -e "$cp_src" ] || continue
        case ${cp_src#.claude/} in worktrees | settings.local.json | CLAUDE.local.md | CLAUDE.md | rules) continue ;; esac
        cp -R "$cp_src" "$cp_tmp/.claude/"
      done
    fi
    # Package install scripts never run (npm_config_ignore_scripts).
    cp_version=$(cd "$cp_tmp" && npm_config_ignore_scripts=true npx --yes rulesync@latest --version) || cp_version=
    cp_version=$(printf '%s\n' "$cp_version" | tail -n 1)
    case $cp_version in
      [0-9]*.[0-9]*.[0-9]*) ;;
      *) echo "codex-port: cannot run rulesync from npm (offline?); the Codex files are unchanged" >&2; return 1 ;;
    esac
    (cd "$cp_tmp" && npm_config_ignore_scripts=true npx --yes "rulesync@$cp_version" convert \
      --from claudecode --to codexcli --features "$cp_features" --silent)
    # rulesync drops disable-model-invocation; Codex reads the same intent from agents/openai.yaml.
    for cp_src in .claude/skills/*/SKILL.md; do
      [ -f "$cp_src" ] || continue
      sed -n '2,/^---$/p' "$cp_src" | grep -q '^disable-model-invocation: *true' || continue
      cp_policy="$cp_tmp/.agents/skills/$(basename "$(dirname "$cp_src")")/agents/openai.yaml"
      if [ -d "$(dirname "$(dirname "$cp_policy")")" ] && [ ! -f "$cp_policy" ]; then
        mkdir -p "$(dirname "$cp_policy")"
        printf 'policy:\n  allow_implicit_invocation: false\n' >"$cp_policy"
      fi
    done
    if ! cp_outputs "$cp_tmp"; then
      echo "codex-port: rulesync $cp_version did not produce the expected files; the Codex files are unchanged" >&2
      return 1
    fi
    # Only .agents and .codex are taken: AGENTS.md is a source, never output.
    cp_list=$(cd "$cp_tmp" && for cp_out in .agents .codex; do
      if [ -e "$cp_out" ]; then find "$cp_out" -type f; fi
    done | sort)
  fi

  if [ "$cp_dry" = 1 ]; then
    if [ -n "$cp_list" ]; then
      echo "codex-port: rulesync $cp_version would write:"
      printf '%s\n' "$cp_list"
    else
      echo "codex-port: nothing to convert in .claude/ or .mcp.json; the instruction files are in order"
    fi
    return 0
  fi

  # Never overwrite a file this block did not write: rulesync would replace it without a word.
  printf '%s\n' "$cp_list" | while IFS= read -r cp_path; do
    [ -n "$cp_path" ] && [ -f "$cp_path" ] || continue
    if [ -f "$cp_manifest" ] && grep -qxF "$cp_path" "$cp_manifest"; then continue; fi
    if [ "$cp_force" = 0 ]; then
      echo "codex-port: $cp_path was not written by codex-port; fold what it holds into the Claude Code sources, then remove it or pass --force" >&2
      exit 1
    fi
  done

  # Remove what the previous run wrote, so outputs whose source is gone disappear. An older
  # manifest may list AGENTS.md: it is a source now, and stays.
  if [ -f "$cp_manifest" ]; then
    while IFS= read -r cp_path; do
      case $cp_path in
        *..*) ;;
        .agents/* | .codex/*) rm -f "$cp_path" ;;
      esac
    done <"$cp_manifest"
    find .agents .codex -type d -empty -delete 2>/dev/null || true
  fi
  if [ -z "$cp_list" ]; then
    echo "codex-port: nothing to convert in .claude/ or .mcp.json; the instruction files are in order"
    return 0
  fi
  printf '%s\n' "$cp_list" | while IFS= read -r cp_path; do
    mkdir -p "$(dirname "$cp_path")"
    cp "$cp_tmp/$cp_path" "$cp_path"
  done
  { echo "# codex-port: rulesync $cp_version"; { echo "$cp_list"; echo "$cp_manifest"; } | sort; } >"$cp_tmp/manifest"
  mkdir -p .codex
  cp "$cp_tmp/manifest" "$cp_manifest"

  cp_outputs .
  echo "codex-port: rulesync $cp_version wrote $cp_skills skills and $cp_agents agents ($(grep -vc '^#' "$cp_manifest") files, listed in $cp_manifest)"
)
# <<< codex-port <<<
