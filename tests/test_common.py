"""Tests for ui/common.py helpers and view event_on_cursor."""

from __future__ import annotations

from datetime import date, datetime

from tuical import store
from tuical.ui import common
from tuical.ui import day as day_view
from tuical.ui import month as month_view
from tuical.ui import week as week_view


def test_week_start_monday():
    assert common.week_start(date(2026, 9, 23)) == date(2026, 9, 21)  # Mon
    assert common.week_start(date(2026, 9, 27)) == date(2026, 9, 21)  # Sun -> back to Mon


def test_shift_month_normal():
    assert common.shift_month(2026, 1, 1) == (2026, 2)
    assert common.shift_month(2026, 12, 1) == (2027, 1)
    assert common.shift_month(2026, 1, -1) == (2025, 12)


def test_shift_day_within_view():
    assert common.shift_day(2026, 9, date(2026, 9, 15), 1) == date(2026, 9, 16)
    assert common.shift_day(2026, 9, date(2026, 9, 1), -1) == date(2026, 8, 31)


def test_shift_day_clamps_day_to_view():
    # day 31 stays valid in month with 31 days, drops to 30 in 30-day month
    assert common.shift_day(2026, 9, date(2026, 9, 30), 1) == date(2026, 10, 1)
    assert common.shift_day(2026, 4, date(2026, 4, 30), 1) == date(2026, 5, 1)


def test_hour_range_expands_for_early_event():
    events = [store.make_event("early", datetime(2026, 1, 1, 6, 0))]
    lo, hi = common.hour_range(events, hour_start=8, hour_end=22)
    assert lo == 6
    assert hi == 22


def test_hour_range_expands_for_late_event():
    events = [store.make_event("late", datetime(2026, 1, 1, 23, 0))]
    lo, hi = common.hour_range(events, hour_start=8, hour_end=22)
    assert lo == 8
    assert hi >= 23


def test_hour_range_ignores_all_day():
    events = [store.make_all_day("holiday", date(2026, 4, 13))]
    lo, hi = common.hour_range(events, hour_start=8, hour_end=22)
    assert lo == 8
    assert hi == 22


def test_last_of_month():
    assert common.last_of_month(2026, 2) == date(2026, 2, 28)
    assert common.last_of_month(2024, 2) == date(2024, 2, 29)
    assert common.last_of_month(2026, 4) == date(2026, 4, 30)


def _state(events: list, cursor: date) -> object:
    from dataclasses import dataclass, field

    @dataclass
    class S:
        events: list = field(default_factory=list)
        view_year: int = 0
        view_month: int = 0
        cursor: date = field(default_factory=date.today)
        mode: str = "month"
        prev_mode: str = "month"
        pending_key: object = None
        form: object = None
        status: str = ""
        quit: bool = False

    s = S(events=events, cursor=cursor, view_year=cursor.year, view_month=cursor.month)
    return s


def test_month_event_on_cursor_returns_first_of_day():
    d = date(2026, 9, 23)
    e1 = store.make_event("first", datetime(2026, 9, 23, 8, 0))
    e2 = store.make_event("second", datetime(2026, 9, 23, 10, 0))
    s = _state([e2, e1], d)
    assert month_view.event_on_cursor(s).summary == "first"


def test_week_event_on_cursor_returns_first_of_day():
    d = date(2026, 9, 23)
    e1 = store.make_event("a", datetime(2026, 9, 23, 9, 0))
    e2 = store.make_event("b", datetime(2026, 9, 24, 10, 0))
    s = _state([e2, e1], d)
    assert week_view.event_on_cursor(s).summary == "a"


def test_day_event_on_cursor_returns_first_of_day():
    d = date(2026, 9, 23)
    e = store.make_event("only", datetime(2026, 9, 23, 9, 0))
    s = _state([e], d)
    assert day_view.event_on_cursor(s).summary == "only"
