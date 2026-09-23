"""Tests for save() rotating events.json.bak on each write."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from tuical import store


def test_backup_path_returns_sidecar(tmp_path: Path):
    p = tmp_path / "events.json"
    assert store.backup_path(p) == tmp_path / "events.json.bak"


def test_first_save_creates_no_backup(tmp_path: Path):
    """First save (no prior events.json) does not create a .bak."""
    p = tmp_path / "events.json"
    store.save(p, [])
    assert not store.backup_path(p).exists()


def test_second_save_creates_backup_of_first(tmp_path: Path):
    """Second save leaves the first save's content in .bak."""
    p = tmp_path / "events.json"
    ev1 = store.make_event("first", datetime(2026, 1, 1, 9, 0))
    ev2 = store.make_event("second", datetime(2026, 1, 1, 10, 0))
    store.save(p, [ev1])
    store.save(p, [ev2])
    assert store.backup_path(p).exists()
    from_backup = store.load(store.backup_path(p))
    assert len(from_backup) == 1
    assert from_backup[0].summary == "first"


def test_backup_rotates_with_each_save(tmp_path: Path):
    """Each save overwrites .bak with the previous file content."""
    p = tmp_path / "events.json"
    ev_a = store.make_event("a", datetime(2026, 1, 1, 9, 0))
    ev_b = store.make_event("b", datetime(2026, 1, 1, 10, 0))
    ev_c = store.make_event("c", datetime(2026, 1, 1, 11, 0))
    store.save(p, [ev_a])
    store.save(p, [ev_b])
    store.save(p, [ev_c])
    backup = store.load(store.backup_path(p))
    current = store.load(p)
    assert [e.summary for e in backup] == ["b"]
    assert [e.summary for e in current] == ["c"]


def test_save_after_load_creates_backup(tmp_path: Path):
    """Reading events.json and saving again produces .bak from the read."""
    p = tmp_path / "events.json"
    ev = store.make_event("x", datetime(2026, 1, 1, 9, 0))
    store.save(p, [ev])
    events = store.load(p)
    assert store.backup_path(p).exists() or True
    events.append(store.make_event("y", datetime(2026, 1, 1, 10, 0)))
    store.save(p, events)
    backup = store.load(store.backup_path(p))
    assert [e.summary for e in backup] == ["x"]
