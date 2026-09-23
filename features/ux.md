# UX overlays

Three in-terminal overlays: search, command palette, help. Plus the
NO_COLOR fallback behavior.

## Search (`/`)

Opens a bottom input line. Type to filter; `Enter` jumps cursor to
first matching event. `Esc` cancels.

- **Match rule:** case-insensitive substring on `summary`
- **Scope:** all events (not filtered by view period — `/foo` finds
  events anywhere in the calendar)
- **Behavior:**
  - Incremental: cursor jumps to first match as you type
  - `Enter` confirms the jump and dismisses the line
  - `Esc` reverts cursor to position before `/` was pressed (snapshot
    at open time)
  - No match → status message `no match for "foo"`; cursor unchanged
- **Display:** matched substring highlighted in agenda view (v1.0+
  when cursor lands in agenda — v0.x only jumps)

## Command palette (`:`)

Bottom input line. Subset of vim's `:`, terse syntax.

| Command | Action |
|---|---|
| `goto YYYY-MM-DD` | move cursor (and view) to that date |
| `export <path>` | write all events to `<path>` as RFC 5545 |
| `import <path>` | read events from `<path>` (RFC 5545 VEVENT only) |
| `quit` | save and quit |

- `Enter` submits; `Esc` cancels
- Unknown command → status message `unknown command: <cmd>`
- Path can be absolute or relative (resolved against cwd)
- `export` overwrites; `import` merges (new events get fresh UUIDs on
  collision — see `features/ics.md`)

## Help overlay (`?`)

Auto-generated from `ui/keymap.py::KEYMAP`. Single source of truth:
the same dict drives both `app.py`'s dispatch and the help text, so
they can't drift.

- Centered title at `y=0`: ` Help — press Esc/q/? to dismiss `
- Body lines stacked from `y = max(2, (h - len) // 2)`
- Width: `min(w - 2, 60)`, horizontal-centered
- Scroll: not implemented (short enough to fit in any reasonable
  terminal — 16 lines on v0.6)
- Dismiss: `Esc` / `q` / `?` / `Enter` / any arrow — writes
  `state.mode = state.prev_mode` so it returns to whichever view
  opened it (month → back to month, never loses context)

## Help overlay rendering

```python
from .keymap import KEYMAP, render_help
HELP_TEXT = render_help(KEYMAP)   # module-level — rendered once
```

Tested by `tests/test_keymap.py::test_help_text_matches_rendered_keymap`
which asserts `ui/help.HELP_TEXT == keymap.render_help(KEYMAP)`.

## Confirm prompts

Single-line yes/no style:

```
Delete "team standup"? (y/N)
```

- `y` (or `Y`) confirms
- Any other key cancels silently (no status message — `Esc` is the
  universal cancel and shouldn't chatter)
- Used by delete (`D`); could be reused for "quit without save"
  prompt in future

## Status messages

`state.status: str` — last action result, displayed in status bar for
3 seconds (handled by `app.py`'s timestamp check). Cleared on next
user action or after timeout.

Examples:

- `imported 7 events from cal.ics`
- `no match for "foo"`
- `saved events.json`
- `unknown command: gott`

## NO_COLOR / mono terminals

When `cfg.use_color` is False (set by `NO_COLOR=1` or when curses
color init fails):

- `init_colors()` is **skipped** entirely
- `COLORS` dict still works — values fall back to plain attrs:
  - `COLORS["today"]`  → `A_BOLD`
  - `COLORS["weekend"]` → `A_DIM` (subtle, can't be bold on mono)
  - `COLORS["allday"]`  → `A_DIM`
  - `COLORS["title"]`   → `A_BOLD`
  - `COLORS["dim"]`     → `A_DIM`
  - `COLORS["status"]`  → `A_REVERSE` (status bar still distinguishable)
  - `COLORS["block_*"]` → `A_NORMAL` (no bg color available)
- Cursor reverse (`A_REVERSE`) still works — it's the primary way to
  show position on mono terminals
- Keybindings unchanged; behavior identical

## Mouse

Not supported (curses mouse events unused). Roadmap item.
