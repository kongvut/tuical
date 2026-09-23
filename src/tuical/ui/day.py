"""Day view: single-day hourly grid with event blocks."""

from __future__ import annotations

import contextlib
import curses
from datetime import date, timedelta

from .. import store
from . import common


def _event_rows(timed: list[store.Event]) -> dict[int, list[tuple[store.Event, bool]]]:
    """Map hour-row index → list of (event, is_first_row) covering that row."""
    rows: dict[int, list[tuple[store.Event, bool]]] = {}
    for ev in timed:
        start_excl = ev.start.hour
        end_excl = ev.end.hour + (1 if ev.end.minute or ev.end.second else 0)
        if end_excl <= start_excl:
            end_excl = start_excl + 1
        for hour in range(start_excl, end_excl):
            is_first = hour == start_excl
            rows.setdefault(hour, []).append((ev, is_first))
    return rows


def render(stdscr, state, cfg, h: int, w: int) -> None:
    d = state.cursor
    dow = d.weekday()
    title_attr = common.COLORS["today"] if d == date.today() else common.COLORS.get(
        "title", curses.A_BOLD
    )
    with contextlib.suppress(curses.error):
        stdscr.addnstr(
            0,
            0,
            f" {common.WEEKDAY_FULL[dow]} {d.isoformat()} "[: w - 1].center(w),
            w - 1,
            title_attr,
        )

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
            stdscr.addnstr(row, 0, "all-day", time_col, common.COLORS["dim"])
        for i, ev in enumerate(all_day[:3]):
            text = f" {ev.summary[: content_w - 2]}"
            with contextlib.suppress(curses.error):
                stdscr.addnstr(
                    row,
                    time_col + 1 + i * (content_w // min(3, len(all_day))),
                    text[: content_w // min(3, len(all_day))],
                    content_w // min(3, len(all_day)),
                    common.COLORS["block_allday_bg"],
                )
        row += 1
        with contextlib.suppress(curses.error):
            stdscr.hline(row, 0, curses.ACS_HLINE, w)
        row += 1

    h_lo, h_hi = common.hour_range(timed, cfg.hour_start, cfg.hour_end)
    with contextlib.suppress(curses.error):
        stdscr.hline(row, 0, curses.ACS_HLINE, w)
    row += 1

    event_rows = _event_rows(timed)
    for hour in range(h_lo, h_hi):
        y = row + (hour - h_lo)
        if y >= h - 1:
            break
        with contextlib.suppress(curses.error):
            stdscr.addnstr(y, 0, f"{hour:02d}:00", time_col, common.COLORS["dim"])
        blocks = event_rows.get(hour, [])
        if not blocks:
            continue
        ev, is_first = blocks[0]
        if is_first:
            time_str = f"{ev.start.strftime('%H:%M')}-{ev.end.strftime('%H:%M')}"
            text = f" {time_str}  {ev.summary}"
        else:
            text = "  ▎"
        with contextlib.suppress(curses.error):
            stdscr.addnstr(
                y,
                content_left,
                text[:content_w].ljust(content_w),
                content_w,
                common.COLORS["block_timed_bg"],
            )

    if not timed and not all_day:
        msg = " no events — press Enter to add  ·  /  search  ·  : palette  "
        with contextlib.suppress(curses.error):
            stdscr.addnstr(
                row + 3,
                0,
                msg[: w - 1].center(w),
                w - 1,
                common.COLORS["dim"],
            )

    nav_hint = "  nav: hl · j/k/n/N day · g today  "
    with contextlib.suppress(curses.error):
        stdscr.addnstr(h - 1, 0, nav_hint[: w - 1], w - 1, common.COLORS["dim"])


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
        pass
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
