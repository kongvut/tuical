r"""Regression test for the `python -m tuical` launch path.

v0.1.0 shipped without `curses.wrapper`, so every launch crashed with
`TypeError: main() missing 1 required positional argument: 'stdscr'`.
This test guards against that regression by patching `curses.wrapper` and
asserting that `entry()` actually routes through it.
"""

from __future__ import annotations

from unittest import mock


def test_entry_calls_curses_wrapper_with_main():
    """Regression: v0.1.0 — main() called without stdscr → TypeError."""
    from tuical import __main__ as m

    with mock.patch.object(m.curses, "wrapper") as mock_wrapper, mock.patch.object(
        m, "main"
    ) as mock_main:
        m.entry()
        mock_wrapper.assert_called_once_with(mock_main)


def test_entry_does_not_call_main_directly():
    """main() must be invoked through curses.wrapper, never bare."""
    from tuical import __main__ as m

    with mock.patch.object(m.curses, "wrapper") as mock_wrapper, mock.patch.object(
        m, "main"
    ) as mock_main:
        mock_wrapper.side_effect = lambda fn: fn()
        m.entry()
        mock_main.assert_called_once()
