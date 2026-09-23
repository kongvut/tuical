"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw not in ("0", "false", "False", "no", "")


@dataclass(frozen=True)
class Config:
    data_path: Path
    tz: ZoneInfo
    hour_start: int
    hour_end: int
    h24: bool
    use_color: bool

    @classmethod
    def load(cls) -> Config:
        return cls(
            data_path=Path(_env("TUICAL_DATA", "~/.config/tuical/events.json")).expanduser(),
            tz=ZoneInfo(_env("TUICAL_TZ", "Asia/Bangkok")),
            hour_start=_env_int("TUICAL_HOUR_START", 8),
            hour_end=_env_int("TUICAL_HOUR_END", 22),
            h24=_env_bool("TUICAL_24H", True),
            use_color=_env_bool("NO_COLOR", True) and "NO_COLOR" not in os.environ,
        )
