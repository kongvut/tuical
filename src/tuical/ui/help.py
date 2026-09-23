"""Help overlay: static keybinding table."""

from __future__ import annotations

import contextlib
import curses

from .. import store
from . import common

HELP_TEXT = """\
  tuical — keybindings

  q / Ctrl-C     quit
  hjkl / arrows  move cursor (mode-adaptive)
  g / G          today / end of period
  y m w d a      switch view (year/month/week/day/agenda)
  n / N          next / prev period
  t / + / -      today / forward 1 / back 1
  Enter          add event at cursor
  e              edit event at cursor
  D              delete event at cursor
  /              search by summary
  :              command palette (goto/export/import/quit)
"""


def render(stdscr, state, cfg, h: int, w: int) -> None:
    title = " Help — press Esc/q/? to dismiss "[: w - 1]
    with contextlib.suppress(curses.error):
        stdscr.addnstr(0, 0, title.center(w), w - 1, common.COLORS.get("title", curses.A_BOLD))
    lines = HELP_TEXT.splitlines()
    y_start = max(2, (h - len(lines)) // 2)
    width = max(10, min(w - 2, 60))
    x_start = max(0, (w - width) // 2)
    for i, line in enumerate(lines):
        y = y_start + i
        if y >= h - 1:
            break
        attr = common.COLORS["title"] if line.strip().startswith("tuical") else curses.A_NORMAL
        with contextlib.suppress(curses.error):
            stdscr.addnstr(y, x_start, line[:width], width, attr)


def handle(state, key: int) -> None:
    if key in (27, ord("q"), ord("?"), 10, 13, curses.KEY_ENTER):
        state.mode = state.prev_mode


def event_on_cursor(state) -> store.Event | None:
    return None
