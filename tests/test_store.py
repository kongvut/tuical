"""Tests for Event model and JSON store round-trip."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from tuical import store


def test_event_validates_end_after_start():
    start = datetime(2026, 1, 1, 9, 0)
    end = datetime(2026, 1, 1, 10, 0)
    ev = store.Event(summary="x", start=start, end=end, all_day=False)
    assert ev.id
    assert ev.summary == "x"


def test_event_rejects_end_before_start():
    try:
        store.Event(
            summary="x",
            start=datetime(2026, 1, 1, 10, 0),
            end=datetime(2026, 1, 1, 9, 0),
            all_day=False,
        )
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_event_requires_summary():
    try:
        store.Event(
            summary="",
            start=datetime(2026, 1, 1, 9, 0),
            end=datetime(2026, 1, 1, 10, 0),
            all_day=False,
        )
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_make_event_default_duration():
    ev = store.make_event("mtg", datetime(2026, 1, 1, 9, 0))
    assert ev.end == datetime(2026, 1, 1, 10, 0)
    assert ev.all_day is False


def test_make_event_custom_end():
    ev = store.make_event("long", datetime(2026, 1, 1, 9, 0), datetime(2026, 1, 1, 12, 30))
    assert ev.end == datetime(2026, 1, 1, 12, 30)


def test_make_all_day_spans_day():
    ev = store.make_all_day("holiday", date(2026, 4, 13))
    assert ev.all_day is True
    assert ev.start == datetime(2026, 4, 13, 0, 0)
    assert ev.end == datetime(2026, 4, 13, 23, 59, 59, 999999)


def test_save_load_roundtrip(tmp_path: Path):
    path = tmp_path / "events.json"
    ev1 = store.Event(
        summary="standup",
        start=datetime(2026, 9, 1, 9, 30),
        end=datetime(2026, 9, 1, 10, 0),
        all_day=False,
        id="abc",
    )
    ev2 = store.make_all_day("songkran", date(2026, 4, 13))
    store.save(path, [ev1, ev2])

    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert len(data["events"]) == 2

    loaded = store.load(path)
    assert len(loaded) == 2
    assert loaded[0].id == "abc"
    assert loaded[0].summary == "standup"
    assert loaded[0].start == datetime(2026, 9, 1, 9, 30)
    assert loaded[1].all_day is True


def test_load_missing_returns_empty(tmp_path: Path):
    assert store.load(tmp_path / "nope.json") == []


def test_save_creates_parent_dirs(tmp_path: Path):
    path = tmp_path / "deep" / "events.json"
    store.save(path, [store.make_event("a", datetime(2026, 1, 1, 9, 0))])
    assert path.exists()


def test_save_writes_atomically(tmp_path: Path):
    """No leftover .tmp file after save."""
    path = tmp_path / "events.json"
    store.save(path, [])
    assert not (path.parent / (path.name + ".tmp")).exists()
    assert not path.with_suffix(path.suffix + ".tmp").exists()


def test_preserves_unicode_summary(tmp_path: Path):
    path = tmp_path / "events.json"
    store.save(path, [store.make_event("นัดหมาย ☕", datetime(2026, 1, 1, 9, 0))])
    loaded = store.load(path)
    assert loaded[0].summary == "นัดหมาย ☕"
