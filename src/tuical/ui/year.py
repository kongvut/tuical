"""Year view: 3x4 grid of mini months."""

from __future__ import annotations

import calendar
import contextlib
import curses
from datetime import date

from .. import store
from . import common


def render(stdscr, state, cfg, h: int, w: int) -> None:
    with contextlib.suppress(curses.error):
        stdscr.addnstr(
            0, 0, f" {state.view_year} "[: w - 1].center(w), w - 1,
            common.COLORS.get("title", curses.A_BOLD),
        )

    cols, rows = 3, 4
    cell_w = max(20, (w - 2) // cols)
    cell_h = max(6, (h - 4) // rows)

    today = date.today()
    events_by_day: dict[date, int] = {}
    for ev in state.events:
        events_by_day[ev.start.date()] = events_by_day.get(ev.start.date(), 0) + 1

    cal = calendar.Calendar(firstweekday=0)
    for idx in range(12):
        r = idx // cols
        c = idx % cols
        y_off = 2 + r * cell_h
        x_off = 1 + c * cell_w
        month = idx + 1
        is_cursor = state.view_year == state.cursor.year and month == state.cursor.month
        is_today = state.view_year == today.year and month == today.month
        weeks = cal.monthdayscalendar(state.view_year, month)
        head_attr = curses.A_NORMAL
        if is_cursor:
            head_attr |= curses.A_REVERSE
        if is_today:
            head_attr |= common.COLORS["today"]
        head = f"{common.MONTH_NAMES[month][:3]} '{state.view_year % 100:02d}"
        with contextlib.suppress(curses.error):
            stdscr.addnstr(y_off, x_off, head.ljust(cell_w)[:cell_w], cell_w, head_attr)
        for wi, week in enumerate(weeks):
            wy = y_off + 1 + wi
            if wy >= y_off + cell_h or wy >= h - 2:
                break
            cells: list[str] = []
            for day in week:
                if day == 0:
                    cells.append("  .")
                elif date(state.view_year, month, day) == today:
                    cells.append(" T ")
                else:
                    cells.append(f"{day:>3}")
            with contextlib.suppress(curses.error):
                stdscr.addnstr(wy, x_off, "".join(cells)[:cell_w], cell_w, common.COLORS["dim"])

    nav_hint = "  nav: hjkl month · n/N year · g today · t/+/-  "
    with contextlib.suppress(curses.error):
        stdscr.addnstr(h - 1, 0, nav_hint[: w - 1], w - 1, common.COLORS["dim"])


def handle(state, key: int) -> None:
    cur = state.cursor
    if key in (ord("h"), curses.KEY_LEFT):
        if cur.month > 1:
            state.cursor = common.safe_replace(cur, month=cur.month - 1)
    elif key in (ord("l"), curses.KEY_RIGHT):
        if cur.month < 12:
            state.cursor = common.safe_replace(cur, month=cur.month + 1)
    elif key in (ord("j"), curses.KEY_DOWN):
        if cur.month <= 9:
            state.cursor = common.safe_replace(cur, month=cur.month + 3)
    elif key in (ord("k"), curses.KEY_UP):
        if cur.month >= 4:
            state.cursor = common.safe_replace(cur, month=cur.month - 3)
    elif key == ord("n"):
        state.view_year += 1
        state.cursor = common.safe_replace(cur, year=state.view_year)
    elif key == ord("N"):
        state.view_year -= 1
        state.cursor = common.safe_replace(cur, year=state.view_year)
    elif key in (ord("g"), ord("t")):
        t = date.today()
        state.view_year, state.cursor = t.year, t
    elif key == ord("G"):
        state.cursor = common.last_of_month(cur.year, 12)


def event_on_cursor(state) -> store.Event | None:
    target_year = state.cursor.year
    target_month = state.cursor.month
    for ev in sorted(state.events, key=lambda e: e.start):
        if ev.start.year == target_year and ev.start.month == target_month:
            return ev
    return None
