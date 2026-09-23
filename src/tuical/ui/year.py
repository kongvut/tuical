"""Year view: 3x4 grid of mini months."""

from __future__ import annotations

import contextlib
import curses
from datetime import date

from .. import store
from . import common


def render(stdscr, state, cfg, h: int, w: int) -> None:
    title = f" {state.view_year} "
    with contextlib.suppress(curses.error):
        stdscr.addnstr(0, 0, title.center(w), w - 1, curses.A_BOLD)

    cols, rows = 3, 4
    cell_w = max(20, (w - 2) // cols)
    cell_h = max(6, (h - 4) // rows)

    today = date.today()
    for idx in range(12):
        r = idx // cols
        c = idx % cols
        y_off = 2 + r * cell_h
        x_off = 1 + c * cell_w
        month = idx + 1
        lines = common.mini_month_lines(state.view_year, month)
        is_cursor = state.view_year == state.cursor.year and month == state.cursor.month
        is_today = state.view_year == today.year and month == today.month
        head_attr = curses.A_NORMAL
        if is_cursor:
            head_attr |= curses.A_REVERSE
        if is_today:
            head_attr |= curses.A_BOLD
        for li, text in enumerate(lines):
            wy = y_off + li
            if wy >= y_off + cell_h or wy >= h - 2:
                break
            attr = head_attr if li == 0 else curses.A_NORMAL
            with contextlib.suppress(curses.error):
                stdscr.addnstr(wy, x_off, text.ljust(cell_w)[:cell_w], cell_w, attr)

    with contextlib.suppress(curses.error):
        stdscr.addnstr(
            h - 1,
            0,
            " Enter:add e:edit D:del n/N:year hjkl:month g:today y/m/w/d/a:view ?:help q:quit ",
            w - 1,
            curses.A_DIM,
        )


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
