"""Shared helpers used by multiple views."""

from __future__ import annotations

import calendar
import curses
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

# Color pairs — populated by init_colors() when the terminal supports them.
# Module-level dict so views can reference common.COLORS["today"] without threading state.
COLORS: dict[str, int] = {}


def init_colors() -> None:
    """Initialize curses color pairs. Falls back to plain attrs on failure."""
    global COLORS
    COLORS = {
        "today": curses.A_BOLD,
        "allday": curses.A_NORMAL,
        "accent": curses.A_BOLD,
        "weekend": curses.A_DIM,
        "warn": curses.A_BOLD | curses.A_REVERSE,
        "status_bg": curses.A_REVERSE,
        "title": curses.A_BOLD,
        "dim": curses.A_DIM,
        "block_timed_bg": curses.A_REVERSE,
        "block_allday_bg": curses.A_NORMAL | curses.A_BOLD,
    }
    try:
        if not curses.has_colors():
            return
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_CYAN, -1)
        curses.init_pair(3, curses.COLOR_BLUE, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        curses.init_pair(5, curses.COLOR_RED, -1)
        curses.init_pair(6, curses.COLOR_MAGENTA, -1)
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_BLUE)
        curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(11, curses.COLOR_BLACK, curses.COLOR_MAGENTA)
        COLORS.update(
            {
                "today": curses.color_pair(1) | curses.A_BOLD,
                "allday": curses.color_pair(2),
                "block_timed_bg": curses.color_pair(9),
                "block_allday_bg": curses.color_pair(8),
                "block_alt_bg": curses.color_pair(10),
                "accent": curses.color_pair(3) | curses.A_BOLD,
                "weekend": curses.color_pair(6),
                "warn": curses.color_pair(5) | curses.A_BOLD,
                "status_bg": curses.color_pair(7) | curses.A_BOLD,
                "title": curses.color_pair(4) | curses.A_BOLD,
                "dim": curses.A_DIM,
            }
        )
    except curses.error:
        pass


def status_bar(mode: str, cursor: date, event_count: int, w: int) -> tuple[str, int]:
    """Return (text, attr) for the unified top status bar."""
    weekday = WEEKDAYS[cursor.weekday()]
    cursor_str = cursor.strftime("%d %b %Y")
    text = (
        f"  {mode.upper():>7}  "
        f"{weekday} {cursor_str}  "
        f"·  cursor {cursor.isoformat()}  "
        f"·  {event_count} event(s)  "
    )
    return text.center(w), COLORS.get("status_bg", curses.A_REVERSE)


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


def safe_replace(
    d: date,
    *,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
) -> date:
    """Like date.replace but clamps day to the new month's last day."""
    y = d.year if year is None else year
    m = d.month if month is None else month
    target_day = d.day if day is None else day
    _, last = calendar.monthrange(y, m)
    return date(y, m, min(target_day, last))


def mini_month_lines(year: int, month: int) -> list[str]:
    """Lines for a 3x4 mini-month cell (header + day rows, no weekday labels)."""
    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdayscalendar(year, month)
    head = f"{MONTH_NAMES[month][:3]} '{year % 100:02d}"
    lines = [head]
    for week in weeks:
        cells = ["  ." if d == 0 else f"{d:>3}" for d in week]
        lines.append("".join(cells))
    return lines
