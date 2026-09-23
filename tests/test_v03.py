"""Tests for v0.3 helpers: year view + agenda view."""

from __future__ import annotations

from datetime import date, datetime

from tuical import store
from tuical.ui import agenda, common


def test_mini_month_lines_header_format():
    lines = common.mini_month_lines(2026, 9)
    assert lines[0] == "Sep '26"
    assert all(len(line) == 21 for line in lines[1:])


def test_mini_month_lines_blank_cells_use_dot():
    # Sep 1 2026 is a Tuesday → first data row starts with one blank then 1
    lines = common.mini_month_lines(2026, 9)
    first = lines[1]
    assert first.startswith("  .  1")
    assert "  ." in first  # dot used for blanks


def test_mini_month_lines_february_leap():
    lines = common.mini_month_lines(2024, 2)
    assert lines[0] == "Feb '24"
    # Feb 2024 has 29 days
    assert "29" in lines[-1]


def test_safe_replace_clamps_day():
    # Jan 31 → Feb (28 or 29)
    d = date(2026, 1, 31)
    assert common.safe_replace(d, month=2) == date(2026, 2, 28)
    assert common.safe_replace(date(2024, 1, 31), month=2) == date(2024, 2, 29)


def test_agenda_events_filters_old_and_sorts():
    today = date(2026, 9, 23)
    old = store.make_event("old", datetime(2026, 1, 1, 9, 0))
    recent_past = store.make_event("recent-past", datetime(2026, 9, 1, 9, 0))
    today_ev = store.make_event("today", datetime(2026, 9, 23, 14, 0))
    future = store.make_event("future", datetime(2026, 10, 1, 9, 0))
    events = [future, old, today_ev, recent_past]
    out = agenda.agenda_events(events, today, past_days=30)
    assert old not in out
    assert [e.summary for e in out] == ["recent-past", "today", "future"]


def test_agenda_events_empty():
    assert agenda.agenda_events([], date(2026, 9, 23)) == []


def test_agenda_events_includes_today():
    today = date(2026, 9, 23)
    ev = store.make_event("today", datetime(2026, 9, 23, 0, 0))
    out = agenda.agenda_events([ev], today, past_days=30)
    assert out == [ev]
