"""Event model + JSON load/save with cross-process locking."""

from __future__ import annotations

import contextlib
import fcntl
import json
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path


@dataclass
class Event:
    summary: str
    start: datetime
    end: datetime
    all_day: bool
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def __post_init__(self) -> None:
        if not isinstance(self.start, datetime) or not isinstance(self.end, datetime):
            raise TypeError("start and end must be datetime")
        if self.end <= self.start:
            raise ValueError("end must be > start")
        if not self.summary:
            raise ValueError("summary must not be empty")


def make_event(summary: str, start: datetime, end: datetime | None = None) -> Event:
    if end is None:
        end = start + timedelta(hours=1)
    return Event(summary=summary, start=start, end=end, all_day=False)


def make_all_day(summary: str, day: date) -> Event:
    start = datetime.combine(day, time.min)
    end = datetime.combine(day, time.max)
    return Event(summary=summary, start=start, end=end, all_day=True)


def lock_path(path: Path) -> Path:
    """Sidecar lock file path: events.json → events.json.lock."""
    return path.with_suffix(path.suffix + ".lock")


def backup_path(path: Path) -> Path:
    """Sidecar backup file path: events.json → events.json.bak."""
    return path.with_suffix(path.suffix + ".bak")


@contextlib.contextmanager
def _flock(path: Path, exclusive: bool):
    """Acquire fcntl flock on a sidecar .lock file.

    Falls back to a no-op on platforms where fcntl is unavailable
    (e.g. Windows). The lock file itself is created if missing.
    """
    op = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    with path.open("a", encoding="utf-8") as lf:
        try:
            fcntl.flock(lf.fileno(), op)
            yield
        except (OSError, AttributeError):
            yield
        finally:
            with contextlib.suppress(OSError, AttributeError):
                fcntl.flock(lf.fileno(), fcntl.LOCK_UN)


def load(path: Path) -> list[Event]:
    if not path.exists():
        return []
    with _flock(lock_path(path), exclusive=False), path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError(f"unsupported store format in {path}")
    out: list[Event] = []
    for raw in data.get("events", []):
        out.append(
            Event(
                id=raw["id"],
                summary=raw["summary"],
                start=datetime.fromisoformat(raw["start"]),
                end=datetime.fromisoformat(raw["end"]),
                all_day=bool(raw.get("all_day", False)),
            )
        )
    return out


def save(path: Path, events: list[Event]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "events": [
            {
                "id": e.id,
                "summary": e.summary,
                "start": e.start.isoformat(),
                "end": e.end.isoformat(),
                "all_day": e.all_day,
            }
            for e in events
        ],
    }
    backup = backup_path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with _flock(lock_path(path), exclusive=True):
        if path.exists():
            backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        tmp.replace(path)
