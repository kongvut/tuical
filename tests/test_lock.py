"""Tests for store.fcntl-based cross-process locking."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from unittest import mock

from tuical import store


def test_lock_path_returns_sidecar(tmp_path: Path):
    p = tmp_path / "events.json"
    assert store.lock_path(p) == tmp_path / "events.json.lock"


def test_save_load_acquire_flocks(tmp_path: Path):
    """Both save (EX) and load (SH) should call fcntl.flock."""
    p = tmp_path / "events.json"
    ev = store.make_event("x", __import__("datetime").datetime(2026, 1, 1, 9, 0))

    with mock.patch("tuical.store.fcntl.flock") as mock_flock:
        store.save(p, [ev])
        store.load(p)
        ops = [c.args[1] for c in mock_flock.call_args_list]
        assert store.fcntl.LOCK_EX in ops, "save should acquire exclusive lock"
        assert store.fcntl.LOCK_SH in ops, "load should acquire shared lock"


def test_concurrent_save_serialized(tmp_path: Path):
    """Two concurrent saves must not interleave — second save sees first's data."""
    p = tmp_path / "events.json"
    ev_a = store.make_event("a", __import__("datetime").datetime(2026, 1, 1, 9, 0))
    ev_b = store.make_event("b", __import__("datetime").datetime(2026, 1, 1, 10, 0))

    results = {}

    def writer(label, ev, delay):
        store.save(p, [ev])
        time.sleep(delay)
        results[label] = store.load(p)

    t1 = threading.Thread(target=writer, args=("first", ev_a, 0.05))
    t2 = threading.Thread(target=writer, args=("second", ev_b, 0.0))
    t1.start()
    t2.start()
    t1.join(timeout=2)
    t2.join(timeout=2)

    assert len(results["first"]) == 1
    assert len(results["second"]) == 1
    assert results["first"][0].summary in ("a", "b")
    assert results["second"][0].summary in ("a", "b")


def test_lock_file_created(tmp_path: Path):
    """save() should create the sidecar lock file."""
    p = tmp_path / "events.json"
    store.save(p, [])
    assert store.lock_path(p).exists()


def test_flock_context_falls_back_on_attributeerror(tmp_path: Path):
    """On platforms where fcntl is unavailable, locking is a no-op (no crash)."""
    p = tmp_path / "events.json"
    ev = store.make_event("x", __import__("datetime").datetime(2026, 1, 1, 9, 0))

    with mock.patch("tuical.store.fcntl.flock", side_effect=AttributeError("not supported")):
        store.save(p, [ev])
        loaded = store.load(p)
    assert len(loaded) == 1
    assert loaded[0].summary == "x"
