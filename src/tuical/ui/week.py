"""Week view: 7-day hourly grid."""

from __future__ import annotations

import contextlib
import curses
from datetime import date, timedelta

from .. import store
from . import common

WEEKDAYS = common.WEEKDAYS


def _week_days(cursor: date) -> list[date]:
    start = common.week_start(cursor)
    return [start + timedelta(days=i) for i in range(7)]


def render(stdscr, state, cfg, h: int, w: int) -> None:
    days = _week_days(state.cursor)
    start, end = days[0], days[-1]
    same_month = start.month == end.month
    if same_month:
        title = f" {common.MONTH_NAMES[start.month]} {start.year} — week of {start.isoformat()} "
    else:
        title = (
            f" {common.MONTH_NAMES[start.month]}–{common.MONTH_NAMES[end.month]} "
            f"{start.year} — week of {start.isoformat()} "
        )
    with contextlib.suppress(curses.error):
        stdscr.addnstr(0, 0, title[: w - 1].center(w), w - 1, curses.A_BOLD)

    time_col = 5
    grid_w = max(7, w - time_col - 1)
    col_w = max(1, grid_w // 7)
    grid_left = time_col + 1

    for i, d in enumerate(days):
        x = grid_left + i * col_w
        header = f"{WEEKDAYS[i]} {d.day}"
        with contextlib.suppress(curses.error):
            stdscr.addnstr(1, x, header[:col_w].ljust(col_w), col_w, curses.A_DIM)

    events_by_day: dict[date, list[store.Event]] = {}
    for ev in state.events:
        events_by_day.setdefault(ev.start.date(), []).append(ev)

    h_lo, h_hi = common.hour_range(
        [ev for evs in events_by_day.values() for ev in evs],
        cfg.hour_start,
        cfg.hour_end,
    )

    row = 3
    with contextlib.suppress(curses.error):
        stdscr.hline(2, 0, curses.ACS_HLINE, w)

    all_day_strip: dict[date, list[str]] = {}
    for d in days:
        names = [ev.summary for ev in events_by_day.get(d, []) if ev.all_day]
        all_day_strip[d] = names
    flat = [f"{WEEKDAYS[i]} {names[0]}" for i, d in enumerate(days) if (names := all_day_strip[d])]
    if flat:
        text = "all-day: " + " · ".join(flat)
        with contextlib.suppress(curses.error):
            stdscr.addnstr(row, 0, text[: w - 1], w - 1)
        row += 1
    with contextlib.suppress(curses.error):
        stdscr.hline(row, 0, curses.ACS_HLINE, w)
    row += 1

    hour_row_start = row
    for hour in range(h_lo, h_hi):
        y = hour_row_start + (hour - h_lo)
        if y >= h - 1:
            break
        with contextlib.suppress(curses.error):
            stdscr.addnstr(y, 0, f"{hour:02d}:00", time_col, curses.A_DIM)
        for i, d in enumerate(days):
            x = grid_left + i * col_w
            cell_events = [
                ev for ev in events_by_day.get(d, []) if not ev.all_day and ev.start.hour == hour
            ]
            attr = curses.A_NORMAL
            if d == state.cursor:
                attr |= curses.A_REVERSE
            content = ""
            if cell_events:
                content = "•" + cell_events[0].summary[: col_w - 1]
                if len(cell_events) > 1:
                    content = content[: col_w - 1] + "+"
            with contextlib.suppress(curses.error):
                stdscr.addnstr(y, x, content[:col_w].ljust(col_w), col_w, attr)

    with contextlib.suppress(curses.error):
        stdscr.addnstr(
            h - 1,
            0,
            " Enter:add e:edit D:del n/N:week hjkl:day/week g:today m/w/d/a:view ?:help q:quit ",
            w - 1,
            curses.A_DIM,
        )


def handle(state, key: int) -> None:
    if key in (ord("h"), curses.KEY_LEFT):
        state.cursor = state.cursor - timedelta(days=1)
    elif key in (ord("l"), curses.KEY_RIGHT):
        state.cursor = state.cursor + timedelta(days=1)
    elif key in (ord("j"), curses.KEY_DOWN):
        state.cursor = state.cursor + timedelta(days=7)
    elif key in (ord("k"), curses.KEY_UP):
        state.cursor = state.cursor - timedelta(days=7)
    elif key == ord("n"):
        state.cursor = state.cursor + timedelta(days=7)
    elif key == ord("N"):
        state.cursor = state.cursor - timedelta(days=7)
    elif key in (ord("g"), ord("t")):
        state.cursor = date.today()
    elif key == ord("G"):
        state.cursor = common.week_start(state.cursor) + timedelta(days=6)
    elif key in (ord("+"), ord("=")):
        state.cursor = state.cursor + timedelta(days=1)
    elif key in (ord("-"), ord("_")):
        state.cursor = state.cursor - timedelta(days=1)


def event_on_cursor(state) -> store.Event | None:
    return _first_today(state.events, state.cursor)


def _first_today(events: list[store.Event], d: date) -> store.Event | None:
    for ev in sorted(events, key=lambda e: (e.all_day, e.start)):
        if ev.start.date() == d:
            return ev
    return None
