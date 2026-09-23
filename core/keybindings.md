# Keybindings

Vim-style. Single source of truth: `src/tuical/ui/keymap.py` — both the
`app.py` dispatcher and the `?` help overlay read from the same `KEYMAP`
dict, so the docs never drift from the code.

## Master keymap

| Section | Key | Action |
|---|---|---|
| **quit** | `q` | quit (saves events to disk) |
| | `Ctrl-C` | quit (no save — escape hatch) |
| **navigation** | `h` `j` `k` `l` | move cursor (mode-adaptive delta) |
| | `←` `↓` `↑` `→` | arrow keys — same as h/j/k/l |
| | `g` | jump to today |
| | `G` | jump to end of period (e.g. last day of month) |
| | `t` | today |
| | `+` / `-` | forward 1 / back 1 period |
| **view** | `y` | year view |
| | `m` | month view |
| | `w` | week view |
| | `d` | day view |
| | `a` | agenda view |
| | `?` | help overlay |
| **actions** | `Enter` | add event at cursor |
| | `e` | edit event at cursor |
| | `D` (shift-d) | delete event at cursor (confirm prompt) |
| **search_palette** | `/` | search by summary (case-insensitive substring) |
| | `:` | command palette (`goto`, `export`, `import`, `quit`) |

View-switch keys are **lowercase only** — pressing `Y`/`M`/`W`/`D`/`A`
does nothing. Avoids collisions with future uppercase bindings (e.g.
reserved for commands like `:Write`).

## Esc handler

`Esc` (key code 27) toggles back to the previous view:

```python
state.mode = state.prev_mode
```

Every view stores its name in `prev_mode` before switching (e.g. opening
`?` help from month sets `prev_mode = "month"`, so Esc returns there).
Help overlay also accepts `q`, `?`, `Enter`, or any arrow to dismiss.

## Dispatch order

`app.py::main()` reads `getch()` and dispatches in this order:

1. **Global overlays first** — `?` → help, `/` → search, `:` → palette.
   These short-circuit `handle()` for the underlying view.
2. **View-mode keys** — `y`/`m`/`w`/`d`/`a` switch `state.mode`.
3. **Action keys** — `Enter`/`e`/`D` open form, ignoring view's `handle`.
4. **View-local keys** — finally `state.mode`'s `handle(state, key)`.
   Navigation (`h`/`j`/`k`/`l`/`n`/`N`) is interpreted by the current
   view (month=±1day, week=±1day, year=±1month, etc.) — they all share
   the same keystroke but the delta is per-view.
5. **Unknown keys** — ignored (no error, no status message).

`n` / `N` advance the period the cursor is in (month view → next month,
week view → next week, etc.) while keeping the cursor on the same
day-of-period if it exists in the new period, else end-of-period.

## NO_COLOR

When `cfg.use_color` is False (`NO_COLOR=1` or terminal without color
support), `init_colors()` is skipped. `COLORS` dict still holds
attribute values but resolves to plain `A_BOLD` / `A_DIM` / `A_REVERSE`.
Keybindings are unchanged.
