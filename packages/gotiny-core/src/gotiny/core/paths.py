"""Where the repo is.

Two things need this and each got it wrong in a different way: `.env` resolution
(pydantic-settings resolves relative to the *working directory*, and some recipes
``cd`` first) and the dev playground page (counting ``parents[n]`` from a module
file is off-by-one bait and breaks entirely under a non-editable install).

So: search upward from a starting point, and let an environment variable win.
Returns None rather than guessing when there is no repo -- a packaged deployment
has no repo root, and inventing one produces a path that does not exist.
"""

import os
from pathlib import Path

MARKERS = ("pyproject.toml", "packages")


def find_repo_root(start: Path | None = None) -> Path | None:
    """Nearest ancestor holding both a pyproject.toml and a packages/ directory."""
    override = os.getenv("GOTINY_REPO_ROOT")
    if override:
        return Path(override)
    origin = (start or Path.cwd()).resolve()
    for directory in [origin, *origin.parents]:
        if (directory / MARKERS[0]).exists() and (directory / MARKERS[1]).is_dir():
            return directory
    return None


def env_file() -> Path | None:
    """The .env we should be reading, wherever the process was started."""
    override = os.getenv("GOTINY_ENV_FILE")
    if override:
        return Path(override)
    root = find_repo_root()
    return root / ".env" if root else None


def load_env() -> Path | None:
    """Push .env into ``os.environ``, once, at import.

    pydantic-settings reads .env into the Settings *object* and never touches
    ``os.environ`` -- so every ``os.getenv("GOTINY_...")`` in the codebase
    silently ignored the file. That is nine settings (persona, whisper model and
    compute, multilingual, kokoro cache, STUN, voices file) quietly running on
    defaults no matter what .env said, with nothing logged.

    Real environment variables still win: this only fills in what is unset, so
    ``GOTINY_PERSONA=... just gateway`` still overrides the file.
    """
    path = env_file()
    if not path or not path.exists():
        return None
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:  # pragma: no cover - ships with pydantic-settings
        return None
    load_dotenv(path, override=False)
    return path
