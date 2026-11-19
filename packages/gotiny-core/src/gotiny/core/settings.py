"""Infra configuration only.

Agent *behaviour* (prompt, voice, language, tools) does NOT live here — it lives
in the database as an ``agent_version`` row, so changing a prompt is not a deploy.
See ADR 0003.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from gotiny.core.paths import find_repo_root


def _find_env_file() -> Path | None:
    """Repo-root .env, found from wherever the process started.

    pydantic-settings resolves ``env_file`` against the *working directory*, and
    some recipes run from a subdirectory (``just say`` does ``cd bench``). That
    made .env silently ignored there -- settings fell back to defaults with no
    warning, which is the worst way to end up misconfigured.
    """
    override = os.getenv("GOTINY_ENV_FILE")
    if override:
        return Path(override)
    root = find_repo_root()
    return root / ".env" if root else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GOTINY_", env_file=_find_env_file(), extra="ignore"
    )

    env: Literal["local", "dev", "prod"] = "local"
    log_level: str = "INFO"

    # model servers
    tts_url: str = "ws://127.0.0.1:8081"
    stt_url: str = "http://127.0.0.1:8082"
    llm_base_url: str = "http://127.0.0.1:11434/v1"
    llm_model: str = "qwen2.5:7b"
    llm_api_key: str = "not-needed-for-ollama"

    # default providers, as name@semver registry keys
    tts_provider: str = "kokoro-http@1.0"
    stt_provider: str = "whisper-http@1.0"

    # gateway
    max_concurrent_calls: int = 4
    warm_pool_size: int = 2

    # control plane (week 2)
    database_url: str | None = None
    api_url: str = "http://127.0.0.1:8000"


@lru_cache
def _load() -> Settings:
    return Settings()


settings = _load()
