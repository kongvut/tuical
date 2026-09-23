"""Shared helpers used by multiple views."""

from __future__ import annotations

import calendar
from datetime import date, timedelta

WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
WEEKDAY_FULL = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_NAMES = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def shift_month(view_year: int, view_month: int, delta: int) -> tuple[int, int]:
    m = view_month + delta
    y = view_year
    while m < 1:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    return y, m


def clamp_to_view(view_year: int, view_month: int, cur: date) -> date:
    _, last = calendar.monthrange(view_year, view_month)
    return date(view_year, view_month, min(cur.day, last))


def shift_day(view_year: int, view_month: int, cur: date, days: int) -> date:
    """Move cur by `days` days, rolling the view month/year if needed."""
    target = cur + timedelta(days=days)
    if (target.year, target.month) == (view_year, view_month):
        new_year, new_month = view_year, view_month
    elif (target.year, target.month) < (view_year, view_month):
        new_year, new_month = shift_month(view_year, view_month, -1)
    else:
        new_year, new_month = shift_month(view_year, view_month, 1)
    _, last = calendar.monthrange(new_year, new_month)
    return date(new_year, new_month, min(target.day, last))


def shift_week(view_year: int, view_month: int, cur: date, weeks: int) -> tuple[int, int, date]:
    target = cur + timedelta(days=weeks * 7)
    if (target.year, target.month) == (view_year, view_month):
        return view_year, view_month, target
    new_year, new_month = shift_month(view_year, view_month, 1 if weeks > 0 else -1)
    _, last = calendar.monthrange(new_year, new_month)
    return new_year, new_month, date(new_year, new_month, min(target.day, last))


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def last_of_month(year: int, month: int) -> date:
    _, last = calendar.monthrange(year, month)
    return date(year, month, last)


def hour_range(events: list, hour_start: int, hour_end: int) -> tuple[int, int]:
    """Expand hour range to fit any events outside the configured window."""
    lo, hi = hour_start, hour_end
    for ev in events:
        if ev.all_day:
            continue
        lo = min(lo, ev.start.hour)
        if ev.end.date() > ev.start.date():
            hi = max(hi, 24)
        else:
            hi = max(hi, ev.end.hour + (1 if ev.end.minute or ev.end.second else 0))
    if lo >= hi:
        lo, hi = hour_start, hour_end
    return lo, hi
