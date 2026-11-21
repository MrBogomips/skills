"""Settings of the editorial review: built-in defaults, a user file, a project file, environment, flags.

Precedence, lowest first: built-in default < user file < project file < environment < command-line flag.

- User file: $GEMINI_EDITORIAL_REVIEW_CONFIG, else ${XDG_CONFIG_HOME:-~/.config}/gemini-editorial-review/config.json
- Project file: the nearest `.gemini-editorial-review.json` from the working directory up to the root of its
  git repository (written at that root, or in the working directory outside a repository).

Both files are flat JSON objects with the keys in KEYS. Only `config set` and `config unset` write them.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from er_text import ReviewError

PROJECT_FILE = ".gemini-editorial-review.json"
USER_ENV = "GEMINI_EDITORIAL_REVIEW_CONFIG"
BACKENDS = ("auto", "api", "agy")
THINKING = ("low", "medium", "high")

# key: (default, allowed values or None, description)
KEYS: dict[str, tuple[object, tuple | None, str]] = {
    "backend": ("auto", BACKENDS, "how to reach the model: agy, api, or auto (agy when installed, else api)"),
    "api_model": ("gemini-4-neon", None, "model id for the api backend"),
    "api_thinking": ("high", THINKING, "thinking level for the api backend"),
    "agy_model": ("gemini-4-neon-high", None, "model id for the agy backend (see `agy models`)"),
    "timeout": (900, None, "seconds allowed for one review"),
}
# Environment variables that override the files (flags override them in turn).
ENV = {"backend": "GEMINI_EDITORIAL_BACKEND"}


def user_path() -> Path:
    explicit = os.environ.get(USER_ENV, "").strip()
    if explicit:
        return Path(explicit).expanduser()
    base = os.environ.get("XDG_CONFIG_HOME", "").strip() or str(Path.home() / ".config")
    return Path(base).expanduser() / "gemini-editorial-review" / "config.json"


def _ancestors(cwd: Path) -> list[Path]:
    """cwd and its parents, stopping at the root of its git repository when there is one."""
    chain = []
    for folder in [cwd, *cwd.parents]:
        chain.append(folder)
        if (folder / ".git").exists():
            return chain
    return chain


def project_path(cwd: Path, *, for_writing: bool = False) -> Path | None:
    chain = _ancestors(cwd.resolve())
    for folder in chain:
        if (folder / PROJECT_FILE).is_file():
            return folder / PROJECT_FILE
    if not for_writing:
        return None
    root = chain[-1] if (chain[-1] / ".git").exists() else cwd.resolve()
    return root / PROJECT_FILE


def validate(key: str, value: object, origin: str) -> object:
    if key not in KEYS:
        raise ReviewError(f"unknown setting {key!r} in {origin}; known: {', '.join(KEYS)}.")
    default, allowed, _ = KEYS[key]
    if isinstance(default, int):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ReviewError(f"{key} must be a whole number of seconds ({origin}).") from None
        if value <= 0:
            raise ReviewError(f"{key} must be positive ({origin}).")
        return value
    if not isinstance(value, str) or not value.strip():
        raise ReviewError(f"{key} must be a non-empty string ({origin}).")
    value = value.strip()
    if allowed and value not in allowed:
        raise ReviewError(f"{key} must be one of {', '.join(allowed)} ({origin}), not {value!r}.")
    return value


def read_file(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ReviewError(f"cannot read the settings file {path}: {exc}") from None
    if not isinstance(data, dict):
        raise ReviewError(f"the settings file {path} must hold a JSON object.")
    return {key: validate(key, value, str(path)) for key, value in data.items()}


def effective(cwd: Path) -> dict[str, tuple[object, str]]:
    """Each setting's value and where it came from, before command-line flags."""
    layers = [("user " + str(user_path()), read_file(user_path()))]
    project = project_path(cwd)
    if project:
        layers.append(("project " + str(project), read_file(project)))
    values = {key: (spec[0], "default") for key, spec in KEYS.items()}
    for origin, data in layers:
        for key, value in data.items():
            values[key] = (value, origin)
    for key, var in ENV.items():
        raw = os.environ.get(var, "").strip()
        if raw:
            values[key] = (validate(key, raw, var), "env " + var)
    return values


def target(scope: str, cwd: Path) -> Path:
    return user_path() if scope == "user" else project_path(cwd, for_writing=True)


def write_file(path: Path, data: dict) -> None:
    if not data:
        if path.is_file():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def set_value(scope: str, key: str, raw: str, cwd: Path) -> Path:
    path = target(scope, cwd)
    data = read_file(path)
    data[key] = validate(key, raw, "the command line")
    write_file(path, data)
    return path


def unset_value(scope: str, key: str, cwd: Path) -> Path:
    if key not in KEYS:
        raise ReviewError(f"unknown setting {key!r}; known: {', '.join(KEYS)}.")
    path = target(scope, cwd)
    data = read_file(path)
    data.pop(key, None)
    write_file(path, data)
    return path


def render(cwd: Path) -> str:
    lines = [f"{key} = {value}    ({origin})" for key, (value, origin) in effective(cwd).items()]
    project = project_path(cwd) or project_path(cwd, for_writing=True)
    lines += ["", f"user file:    {user_path()}", f"project file: {project}"]
    lines += ["", "Settings:"] + [f"  {key}: {spec[2]}" + (f" ({'|'.join(spec[1])})" if spec[1] else "")
                                  + f", default {spec[0]}" for key, spec in KEYS.items()]
    return "\n".join(lines)
