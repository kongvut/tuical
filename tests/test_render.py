"""Mock-stdscr tests for view render correctness.

These tests would have caught the v0.6 year-view today/cursor combo bug
(year.py was using = instead of |= when applying the today attr, so
when cursor month == today month the today highlight disappeared).
Pytest covered logic helpers but render output was untested.

The MockStdscr records addnstr/hline calls so tests can assert that the
right (y, x, text, attr) tuples were issued for known inputs.
"""

from __future__ import annotations

import curses
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from tuical import config, store
from tuical.ui import common, day, month, week, year

# curses.ACS_* constants are only populated after curses.initscr(); stub
# them so views that call stdscr.hline(..., curses.ACS_HLINE, ...) work
# outside a real TTY.
curses.ACS_HLINE = ord("-")
curses.ACS_VLINE = ord("|")
curses.ACS_PLUS = ord("+")


@dataclass
class MockStdscr:
    """Minimal curses stdscr replacement that records draw calls."""

    h: int = 24
    w: int = 80
    calls: list[tuple[int, int, str, int]] = field(default_factory=list)
    cells: dict[tuple[int, int], tuple[str, int]] = field(default_factory=dict)

    def getmaxyx(self) -> tuple[int, int]:
        return (self.h, self.w)

    def addnstr(self, y: int, x: int, text: str, n: int, attr: int = 0) -> int:
        self.calls.append((y, x, text, attr))
        for i, c in enumerate(text[:n]):
            self.cells[(y, x + i)] = (c, attr)
        return 0

    def hline(self, y: int, x: int, ch: Any, n: int) -> int:
        for i in range(n):
            self.cells[(y, x + i)] = (ch, 0)
        return 0

    def refresh(self) -> None:
        pass

    def erase(self) -> None:
        self.cells.clear()
        self.calls.clear()

    def keypad(self, _x: bool) -> None:
        pass


def _state(*, cursor=None, view_year=2026, view_month=9, mode="year", events=None) -> Any:
    @dataclass
    class S:
        events: list = field(default_factory=list)
        cursor: date = field(default_factory=date.today)
        view_year: int = 0
        view_month: int = 0
        mode: str = "month"
        prev_mode: str = "month"
        status: str = ""
        cursor_event_idx: int = 0

    c = cursor or date.today()
    return S(
        events=events or [],
        cursor=c,
        view_year=view_year,
        view_month=view_month,
        mode=mode,
    )


def _cfg() -> config.Config:
    return config.Config(
        data_path=Path("/tmp/none.json"),
        tz=config.ZoneInfo("Asia/Bangkok"),
        hour_start=8,
        hour_end=22,
        h24=True,
        use_color=False,
    )


def _init_colors_or_skip():
    try:
        common.init_colors()
        return True
    except Exception:
        return False


def test_year_view_today_attr_when_cursor_equals_today():
    """Regression: cursor=today month must still highlight today (|=, not =).

    Catches the v0.6 bug where `head_attr = COLORS['today']` (replace)
    dropped the A_REVERSE flag set by the cursor branch, so today's
    month lost both the reverse-video cursor highlight AND ended up with
    only the today attr (visually inconsistent with cursor behavior
    in other views).
    """
    if not _init_colors_or_skip():
        return
    today = date.today()
    mock = MockStdscr(h=24, w=80)
    state = _state(cursor=today, view_year=today.year, view_month=today.month, events=[])
    year.render(mock, state, _cfg(), h=24, w=80)

    cell_w = (80 - 2) // 3
    cell_h = max(6, (24 - 4) // 4)  # mirror year.py's max(6, ...) floor
    today_idx = today.month - 1
    sep_y = 2 + (today_idx // 3) * cell_h
    sep_x = 1 + (today_idx % 3) * cell_w
    header_calls = [c for c in mock.calls if c[0] == sep_y and c[1] == sep_x]
    assert header_calls, f"current-month header at ({sep_y},{sep_x}) was not drawn"
    attr = header_calls[0][3]
    assert common.COLORS["today"] & attr, (
        f"header attr 0x{attr:x} missing COLORS['today'] 0x{common.COLORS['today']:x} — "
        "year.py is replacing instead of OR-ing the today attr"
    )
    assert curses.A_REVERSE & attr, (
        f"header attr 0x{attr:x} missing A_REVERSE (0x{curses.A_REVERSE:x}) — cursor=today month "
        "should have BOTH today attr AND reverse video"
    )


def test_year_view_today_attr_when_cursor_different_month():
    """When cursor is not on today's month, today's header still gets today attr."""
    if not _init_colors_or_skip():
        return
    today = date.today()
    other_month = 1 if today.month != 1 else 6
    mock = MockStdscr(h=24, w=80)
    state = _state(
        cursor=date(today.year, other_month, 1),
        view_year=today.year,
        view_month=other_month,
        events=[],
    )
    year.render(mock, state, _cfg(), h=24, w=80)
    cell_w = (80 - 2) // 3
    cell_h = max(6, (24 - 4) // 4)
    today_idx = today.month - 1
    sep_y = 2 + (today_idx // 3) * cell_h
    sep_x = 1 + (today_idx % 3) * cell_w
    header_calls = [c for c in mock.calls if c[0] == sep_y and c[1] == sep_x]
    assert header_calls
    attr = header_calls[0][3]
    assert common.COLORS["today"] & attr


def test_day_view_event_block_has_bg_attr():
    """Day view should render timed events with bg color (event block visual)."""
    if not _init_colors_or_skip():
        return
    d = date(2026, 9, 23)
    ev = store.make_event("mtg", datetime(2026, 9, 23, 9, 0), datetime(2026, 9, 23, 10, 0))
    mock = MockStdscr(h=24, w=80)
    state = _state(cursor=d, view_year=2026, view_month=9, mode="day", events=[ev])
    day.render(mock, state, _cfg(), h=24, w=80)
    block_calls = [c for c in mock.calls if common.COLORS["block_timed_bg"] & c[3]]
    assert block_calls, "no day-view event block with bg color found"


def test_week_view_event_cell_has_bg_attr():
    """Week view should render event cells with bg color."""
    if not _init_colors_or_skip():
        return
    cursor = date(2026, 9, 23)
    ev = store.make_event("mtg", datetime(2026, 9, 23, 10, 0), datetime(2026, 9, 23, 11, 0))
    mock = MockStdscr(h=24, w=80)
    state = _state(cursor=cursor, view_year=2026, view_month=9, mode="week", events=[ev])
    week.render(mock, state, _cfg(), h=24, w=80)
    block_calls = [c for c in mock.calls if common.COLORS["block_timed_bg"] & c[3]]
    assert block_calls, "no week-view event cell with bg color found"


def test_month_view_today_attr_persists_with_cursor():
    """Regression: when cursor=today, month cell must have BOTH today color AND reverse."""
    if not _init_colors_or_skip():
        return
    today = date.today()
    mock = MockStdscr(h=24, w=80)
    state = _state(cursor=today, view_year=today.year, view_month=today.month, events=[])
    month.render(mock, state, _cfg(), h=24, w=80)
    col_w = (80 - 2) // 7
    grid_left = (80 - col_w * 7) // 2
    cal = __import__("calendar").Calendar(firstweekday=0)
    weeks = cal.monthdayscalendar(today.year, today.month)
    week_row = next(i for i, w in enumerate(weeks) if today.day in w)
    today_col = weeks[week_row].index(today.day)
    today_y = 2 + week_row
    today_x = grid_left + today_col * col_w
    cell_calls = [c for c in mock.calls if c[0] == today_y and c[1] == today_x]
    assert cell_calls, f"today cell at ({today_y},{today_x}) not drawn"
    attr = cell_calls[0][3]
    assert common.COLORS["today"] & attr, (
        f"today attr 0x{common.COLORS['today']:x} missing from today cell 0x{attr:x}"
    )
    assert curses.A_REVERSE & attr, "reverse attr missing from today cell when cursor=today"
