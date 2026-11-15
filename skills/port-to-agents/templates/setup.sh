#!/bin/sh
# Sets up a checkout or worktree, locally and on CI.
#
#   ./setup.sh [--ci] [--codex-only] [--dry-run | --check] [--force]
#   --ci          as CI runs it, also when CI is set: install from the lockfile, frozen
#   --codex-only  only regenerate the Codex files
#   --dry-run, --check, --force
#                 passed to codex_port (see its block); they imply --codex-only
#
# It installs no tool: the runtimes come from the developer's machine or from the CI setup.
set -eu
cd "$(dirname "$0")"

fail() {
  echo "setup: $*" >&2
  exit 1
}

# VENDOR: fill in from the lockfile (references/setup-strategies.md) and drop this comment;
# with no lockfile, delete the function and its call in main.
install_dependencies() {
  if [ "$1" = 1 ]; then INSTALL_FROZEN; else INSTALL; fi
}

# VENDOR: replace this line with templates/codex-port-block.sh, verbatim, markers included.

main() {
  ci=0 codex_only=0 codex_args=
  if [ -n "${CI:-}" ]; then ci=1; fi
  for arg in "$@"; do
    case $arg in
      --ci) ci=1 ;;
      --codex-only) codex_only=1 ;;
      --dry-run | --check | --force) codex_only=1 codex_args="$codex_args $arg" ;;
      *) fail "unknown option '$arg' (use --ci, --codex-only, --dry-run, --check or --force)" ;;
    esac
  done
  if [ "$codex_only" = 0 ]; then install_dependencies "$ci"; fi
  # shellcheck disable=SC2086 # codex_args holds whole option words only
  codex_port $codex_args
}

main "$@"
