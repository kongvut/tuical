"""Day view: single-day hourly grid with all-day strip."""

from __future__ import annotations

import contextlib
import curses
from datetime import date, timedelta

from .. import store
from . import common

WEEKDAYS = common.WEEKDAYS
WEEKDAY_FULL = common.WEEKDAY_FULL


def render(stdscr, state, cfg, h: int, w: int) -> None:
    d = state.cursor
    dow = d.weekday()
    title = f" {WEEKDAY_FULL[dow]} {d.isoformat()} "
    with contextlib.suppress(curses.error):
        stdscr.addnstr(0, 0, title.center(w), w - 1, curses.A_BOLD)

    time_col = 6
    content_left = time_col + 1
    content_w = max(1, w - content_left)

    day_events = sorted(
        (ev for ev in state.events if ev.start.date() == d),
        key=lambda e: (e.all_day, e.start),
    )
    all_day = [ev for ev in day_events if ev.all_day]
    timed = [ev for ev in day_events if not ev.all_day]

    row = 2
    if all_day:
        with contextlib.suppress(curses.error):
            stdscr.addnstr(row, 0, "all-day", time_col, curses.A_DIM)
        names = " · ".join(ev.summary for ev in all_day)
        with contextlib.suppress(curses.error):
            stdscr.addnstr(row, content_left, names[: content_w], content_w)
        row += 1
        with contextlib.suppress(curses.error):
            stdscr.hline(row, 0, curses.ACS_HLINE, w)
        row += 1

    h_lo, h_hi = common.hour_range(timed, cfg.hour_start, cfg.hour_end)
    with contextlib.suppress(curses.error):
        stdscr.hline(row, 0, curses.ACS_HLINE, w)
    row += 1

    for hour in range(h_lo, h_hi):
        y = row + (hour - h_lo)
        if y >= h - 1:
            break
        with contextlib.suppress(curses.error):
            stdscr.addnstr(y, 0, f"{hour:02d}:00", time_col, curses.A_DIM)
        in_hour = [
            ev
            for ev in timed
            if ev.start.hour <= hour
            < ev.end.hour + (1 if ev.end.minute or ev.end.second else 0)
        ]
        line = ""
        for ev in in_hour:
            time_str = f"{ev.start.strftime('%H:%M')}-{ev.end.strftime('%H:%M')}"
            line = f"{time_str}  {ev.summary}"
            break
        with contextlib.suppress(curses.error):
            stdscr.addnstr(y, content_left, line[: content_w], content_w)

    with contextlib.suppress(curses.error):
        stdscr.addnstr(
            h - 1,
            0,
            " Enter:add e:edit D:del n/N:day hjkl:day/hour g:today m/w/d/a:view ?:help q:quit ",
            w - 1,
            curses.A_DIM,
        )


def handle(state, key: int) -> None:
    if key in (ord("h"), curses.KEY_LEFT):
        state.cursor = state.cursor - timedelta(days=1)
    elif key in (ord("l"), curses.KEY_RIGHT, ord("j"), curses.KEY_DOWN, ord("n")):
        state.cursor = state.cursor + timedelta(days=1)
    elif key in (ord("k"), curses.KEY_UP, ord("N")):
        state.cursor = state.cursor - timedelta(days=1)
    elif key in (ord("g"), ord("t")):
        state.cursor = date.today()
    elif key == ord("G"):
        pass  # single day, no end-of-period
    elif key in (ord("+"), ord("=")):
        state.cursor = state.cursor + timedelta(days=1)
    elif key in (ord("-"), ord("_")):
        state.cursor = state.cursor - timedelta(days=1)


def event_on_cursor(state) -> store.Event | None:
    events = sorted(state.events, key=lambda e: (e.all_day, e.start))
    for ev in events:
        if ev.start.date() == state.cursor:
            return ev
    return None
