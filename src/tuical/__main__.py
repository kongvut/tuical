"""Entry point for `python -m tuical`.

Wraps `app.main(stdscr)` in `curses.wrapper` so stdscr is provided and the
terminal is reset on exit. The `entry()` function is the testable hook —
the `__main__` guard just calls it.
"""

from __future__ import annotations

import curses

from .app import main


def entry() -> None:
    """Run the TUI under curses.wrapper. Used by both the CLI and tests."""
    curses.wrapper(main)


if __name__ == "__main__":
    entry()
