"""Month view: render and key handling."""

from __future__ import annotations

import calendar
import contextlib
import curses
from datetime import date

from .. import store
from . import common

WEEKDAYS = common.WEEKDAYS


def render(stdscr, state, cfg, h: int, w: int) -> None:
    with contextlib.suppress(curses.error):
        stdscr.addnstr(
            0, 0,
            f" {common.MONTH_NAMES[state.view_month]} {state.view_year} "[: w - 1].center(w),
            w - 1,
            common.COLORS.get("title", curses.A_BOLD),
        )

    col_w = max(3, (w - 2) // 7)
    grid_left = max(0, (w - col_w * 7) // 2)
    for i, lbl in enumerate(WEEKDAYS):
        x = grid_left + i * col_w
        attr = common.COLORS["weekend"] if i >= 5 else common.COLORS["dim"]
        with contextlib.suppress(curses.error):
            stdscr.addnstr(1, x, lbl.center(col_w)[:col_w], col_w, attr)

    events_by_day: dict[date, list[store.Event]] = {}
    for ev in state.events:
        events_by_day.setdefault(ev.start.date(), []).append(ev)

    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdayscalendar(state.view_year, state.view_month)
    today = date.today()
    for row, week in enumerate(weeks[:6]):
        for col, day in enumerate(week):
            if day == 0:
                continue
            y = 2 + row
            x = grid_left + col * col_w
            cell_date = date(state.view_year, state.view_month, day)
            count = len(events_by_day.get(cell_date, []))
            attr = curses.A_NORMAL
            if col >= 5 and cell_date != today:
                attr |= common.COLORS["weekend"]
            if cell_date == today:
                attr |= common.COLORS["today"]
            if cell_date == state.cursor:
                attr |= curses.A_REVERSE
            day_str = f"{day}"
            if count:
                day_str = day_str + "•"
            content = day_str.rjust(col_w - 1) + " "
            with contextlib.suppress(curses.error):
                stdscr.addnstr(y, x, content[:col_w], col_w, attr)

    footer_y = h - 4
    if footer_y > 8:
        with contextlib.suppress(curses.error):
            stdscr.hline(footer_y, 0, curses.ACS_HLINE, w)
        events = sorted(events_by_day.get(state.cursor, []), key=lambda e: e.start)
        head = f" {state.cursor.isoformat()}  {len(events)} event(s) "
        with contextlib.suppress(curses.error):
            stdscr.addnstr(footer_y, 0, head[: w - 1], w - 1, common.COLORS["title"])
        for i, ev in enumerate(events[: max(0, h - footer_y - 2)]):
            time_str = "   " if ev.all_day else ev.start.strftime("%H:%M")
            attr = common.COLORS["allday"] if ev.all_day else curses.A_NORMAL
            line = f"  {time_str}  {ev.summary}"
            with contextlib.suppress(curses.error):
                stdscr.addnstr(footer_y + 1 + i, 0, line[: w - 1], w - 1, attr)

    nav_hint = "  nav: hjkl · n/N month · g today  "
    with contextlib.suppress(curses.error):
        stdscr.addnstr(h - 1, 0, nav_hint[: w - 1], w - 1, common.COLORS["dim"])


def handle(state, key: int) -> None:
    if key in (ord("h"), curses.KEY_LEFT):
        state.cursor = common.shift_day(state.view_year, state.view_month, state.cursor, -1)
    elif key in (ord("l"), curses.KEY_RIGHT):
        state.cursor = common.shift_day(state.view_year, state.view_month, state.cursor, 1)
    elif key in (ord("j"), curses.KEY_DOWN):
        state.cursor = common.shift_day(state.view_year, state.view_month, state.cursor, 7)
    elif key in (ord("k"), curses.KEY_UP):
        state.cursor = common.shift_day(state.view_year, state.view_month, state.cursor, -7)
    elif key in (ord("n"),):
        y, m = common.shift_month(state.view_year, state.view_month, 1)
        state.view_year, state.view_month = y, m
        state.cursor = common.clamp_to_view(y, m, state.cursor)
    elif key in (ord("N"),):
        y, m = common.shift_month(state.view_year, state.view_month, -1)
        state.view_year, state.view_month = y, m
        state.cursor = common.clamp_to_view(y, m, state.cursor)
    elif key in (ord("g"), ord("t")):
        t = date.today()
        state.view_year, state.view_month, state.cursor = t.year, t.month, t
    elif key == ord("G"):
        state.cursor = common.last_of_month(state.view_year, state.view_month)
    elif key in (ord("+"), ord("=")):
        state.cursor = common.shift_day(state.view_year, state.view_month, state.cursor, 1)
    elif key in (ord("-"), ord("_")):
        state.cursor = common.shift_day(state.view_year, state.view_month, state.cursor, -1)


def event_on_cursor(state) -> store.Event | None:
    for ev in sorted(state.events, key=lambda e: e.start):
        if ev.start.date() == state.cursor:
            return ev
    return None
