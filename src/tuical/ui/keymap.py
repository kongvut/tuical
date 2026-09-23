"""Central keybinding map — drives help overlay and view footer hints.

Adding or renaming a key in this dict updates every place that reads it
(help overlay, view footer hints, future dispatch table). The key tuple
format is (display_label, one-line description).
"""

from __future__ import annotations

KEYMAP: dict[str, list[tuple[str, str]]] = {
    "quit": [
        ("q", "quit"),
        ("Ctrl-C", "force quit"),
    ],
    "navigation": [
        ("h / ←", "prev day / prev item"),
        ("j / ↓", "down (week in day mode)"),
        ("k / ↑", "up (week in day mode)"),
        ("l / →", "next day / next item"),
        ("n / N", "next / prev period"),
        ("g / G", "today / end of period"),
        ("t / + / -", "today / forward 1 / back 1"),
        ("Esc", "back to previous view"),
    ],
    "view": [
        ("y", "year view (3x4)"),
        ("m", "month view"),
        ("w", "week view"),
        ("d", "day view"),
        ("a", "agenda view"),
        ("?", "help overlay"),
    ],
    "actions": [
        ("Enter", "add event at cursor"),
        ("e", "edit event at cursor"),
        ("D (shift)", "delete event at cursor (confirm)"),
    ],
    "search_palette": [
        ("/", "search by summary"),
        (":", "command palette (goto / export / import / quit)"),
    ],
}


def render_help(keymap: dict[str, list[tuple[str, str]]] | None = None) -> str:
    """Format the keymap as a multi-section help text block."""
    keymap = keymap or KEYMAP
    lines = ["  tuical — keybindings", ""]
    section_titles = {
        "quit": "quit",
        "navigation": "navigation",
        "view": "view switch",
        "actions": "actions",
        "search_palette": "search & palette",
    }
    for section, items in keymap.items():
        if not items:
            continue
        title = section_titles.get(section, section)
        lines.append(f"  ── {title} {'─' * max(0, 50 - len(title))}")
        for keys, desc in items:
            lines.append(f"    {keys:<18} {desc}")
        lines.append("")
    return "\n".join(lines)


def nav_hint_for(view_mode: str) -> str:
    """Compact nav hint for a view footer — first 4 navigation keys."""
    items = KEYMAP.get("navigation", [])[:4]
    parts = [f"{k}: {d.split(' / ')[0]}" for k, d in items]
    return "  " + " · ".join(parts)
