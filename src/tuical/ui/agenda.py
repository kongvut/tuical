"""Agenda view: flat event list around today."""

from __future__ import annotations

import contextlib
import curses
from datetime import date, timedelta

from .. import store
from . import common

PAST_DAYS = 30


def agenda_events(
    events: list[store.Event],
    today: date,
    past_days: int = PAST_DAYS,
) -> list[store.Event]:
    """Sorted events within [today - past_days, ∞)."""
    lo = today - timedelta(days=past_days)
    return sorted(
        (e for e in events if e.start.date() >= lo),
        key=lambda e: e.start,
    )


def _line(ev: store.Event, width: int) -> str:
    d_str = ev.start.date().isoformat()
    t_str = "all-day" if ev.all_day else f"{ev.start.strftime('%H:%M')}-{ev.end.strftime('%H:%M')}"
    line = f"{d_str}  {t_str:<13}  {ev.summary}"
    return line[: max(0, width - 1)]


def render(stdscr, state, cfg, h: int, w: int) -> None:
    today = date.today()
    events = agenda_events(state.events, today)
    head = (
        f" Agenda — {len(events)} event(s) within {today.isoformat()} ± {PAST_DAYS}d "
    )
    with contextlib.suppress(curses.error):
        stdscr.addnstr(
            0, 0, head[: w - 1].center(w), w - 1, common.COLORS.get("title", curses.A_BOLD)
        )
    with contextlib.suppress(curses.error):
        stdscr.addnstr(
            1, 0, "Date        Time           Summary"[: w - 1], w - 1, common.COLORS["dim"]
        )

    cursor_ev = (
        events[state.cursor_event_idx]
        if 0 <= state.cursor_event_idx < len(events)
        else None
    )

    row = 2
    for ev in events:
        if row >= h - 1:
            break
        attr = curses.A_NORMAL
        if ev is cursor_ev:
            attr |= curses.A_REVERSE
        if ev.all_day:
            attr |= common.COLORS["allday"]
        elif ev.start.date() < today:
            attr |= common.COLORS["weekend"]
        elif ev.start.date() == today:
            attr |= common.COLORS["today"]
        with contextlib.suppress(curses.error):
            stdscr.addnstr(row, 0, _line(ev, w), w - 1, attr)
        row += 1

    if not events:
        with contextlib.suppress(curses.error):
            stdscr.addnstr(2, 0, " (no events)", w - 1, common.COLORS["dim"])

    nav_hint = "  nav: j/k n/N · g today · G last  "
    with contextlib.suppress(curses.error):
        stdscr.addnstr(h - 1, 0, nav_hint[: w - 1], w - 1, common.COLORS["dim"])


def handle(state, key: int) -> None:
    events = agenda_events(state.events, date.today())
    n = len(events)
    if key in (ord("j"), curses.KEY_DOWN, ord("n")):
        if n and state.cursor_event_idx < n - 1:
            state.cursor_event_idx += 1
            _sync_cursor(state, events)
    elif key in (ord("k"), curses.KEY_UP, ord("N")):
        if state.cursor_event_idx > 0:
            state.cursor_event_idx -= 1
            _sync_cursor(state, events)
    elif key in (ord("h"), curses.KEY_LEFT, ord("l"), curses.KEY_RIGHT):
        pass
    elif key in (ord("g"), ord("t")):
        for i, e in enumerate(events):
            if e.start.date() >= date.today():
                state.cursor_event_idx = i
                _sync_cursor(state, events)
                return
        state.cursor_event_idx = max(0, n - 1)
        _sync_cursor(state, events)
    elif key == ord("G"):
        state.cursor_event_idx = max(0, n - 1)
        _sync_cursor(state, events)


def _sync_cursor(state, events: list[store.Event]) -> None:
    if 0 <= state.cursor_event_idx < len(events):
        ev = events[state.cursor_event_idx]
        state.cursor = ev.start.date()
        state.view_year = ev.start.year
        state.view_month = ev.start.month


def event_on_cursor(state) -> store.Event | None:
    events = agenda_events(state.events, date.today())
    if 0 <= state.cursor_event_idx < len(events):
        return events[state.cursor_event_idx]
    return None
