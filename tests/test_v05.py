"""Tests for v0.5 search + help + palette logic (pure helpers, no curses)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from tuical import ical, store


@dataclass
class S:
    events: list = field(default_factory=list)
    cursor: date = field(default_factory=date.today)
    view_year: int = 0
    view_month: int = 0
    mode: str = "month"
    prev_mode: str = "month"
    status: str = ""
    search_buf: str = ""
    palette_buf: str = ""
    cursor_event_idx: int = 0
    quit: bool = False


def _state(events=None, cursor=None) -> S:
    c = cursor or date(2026, 9, 23)
    return S(events=events or [], cursor=c, view_year=c.year, view_month=c.month)


def test_search_finds_event_case_insensitive():
    events = [
        store.make_event("Standup", datetime(2026, 9, 23, 9, 0)),
        store.make_event("Lunch", datetime(2026, 9, 24, 12, 0)),
    ]
    s = _state(events=events)
    s.search_buf = "stand"
    from tuical.app import commit_search
    commit_search(s)
    assert s.cursor == date(2026, 9, 23)
    assert "found" in s.status
    assert "Standup" in s.status


def test_search_no_match():
    events = [store.make_event("foo", datetime(2026, 9, 23, 9, 0))]
    s = _state(events=events)
    s.search_buf = "bar"
    from tuical.app import commit_search
    commit_search(s)
    assert s.status == "no match"


def test_search_empty_needle():
    s = _state()
    s.search_buf = "   "
    from tuical.app import commit_search
    commit_search(s)
    assert "empty" in s.status


def test_palette_goto_valid_date():
    s = _state()
    s.palette_buf = "goto 2026-12-31"
    from tuical.app import commit_palette
    commit_palette(s)
    assert s.cursor == date(2026, 12, 31)
    assert "goto" in s.status


def test_palette_goto_invalid_date():
    s = _state()
    s.palette_buf = "goto not-a-date"
    from tuical.app import commit_palette
    commit_palette(s)
    assert "bad date" in s.status


def test_palette_quit_sets_quit_flag():
    s = _state()
    s.palette_buf = "quit"
    from tuical.app import commit_palette
    commit_palette(s)
    assert s.quit is True


def test_palette_unknown_command():
    s = _state()
    s.palette_buf = "frobnicate"
    from tuical.app import commit_palette
    commit_palette(s)
    assert "unknown" in s.status


def test_palette_export_writes_file(tmp_path: Path):
    events = [store.make_event("x", datetime(2026, 1, 1, 9, 0))]
    s = _state(events=events)
    path = tmp_path / "out.ics"
    s.palette_buf = f"export {path}"
    from tuical.app import commit_palette
    commit_palette(s)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "BEGIN:VCALENDAR" in text
    assert "SUMMARY:x" in text


def test_palette_import_merges_events(tmp_path: Path):
    existing = store.Event(
        summary="old",
        start=datetime(2026, 9, 23, 9, 0),
        end=datetime(2026, 9, 23, 10, 0),
        all_day=False,
        id="keep-me",
    )
    replacement = store.Event(
        summary="updated",
        start=datetime(2026, 9, 23, 9, 0),
        end=datetime(2026, 9, 23, 10, 0),
        all_day=False,
        id="keep-me",
    )
    new_event = store.Event(
        summary="fresh",
        start=datetime(2026, 9, 24, 9, 0),
        end=datetime(2026, 9, 24, 10, 0),
        all_day=False,
        id="new-id",
    )
    path = tmp_path / "in.ics"
    ical.export_to_path(path, [replacement, new_event])
    s = _state(events=[existing])
    s.palette_buf = f"import {path}"
    from tuical.app import commit_palette
    commit_palette(s)
    assert len(s.events) == 2
    by_id = {e.id: e for e in s.events}
    assert by_id["keep-me"].summary == "updated"
    assert by_id["new-id"].summary == "fresh"


def test_palette_import_bad_path():
    s = _state()
    s.palette_buf = "import /nonexistent/path.ics"
    from tuical.app import commit_palette
    commit_palette(s)
    assert "import failed" in s.status


def test_help_text_is_nonempty():
    from tuical.ui.help import HELP_TEXT
    assert len(HELP_TEXT.splitlines()) >= 10
    assert "quit" in HELP_TEXT
    assert "search" in HELP_TEXT
    assert "command palette" in HELP_TEXT
