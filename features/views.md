# Views

5 views, mode-switchable via single-letter keys. All share a top status
bar overlaid by `app.py` at `y=0`.

## Status bar (shared, rendered by `ui/common.py:status_bar`)

```
  [ MONTH]  Wed 23 Sep 2026  ·  cursor 2026-09-23  ·  5 event(s)
```

- Left: mode label in `[]`, padded to fixed width
- Date: human format (`Wed 23 Sep 2026`); cursor date in ISO
- Right: event count (filtered to the period shown, e.g. month view
  shows total events in that month)
- Attr: white-on-blue bg (or `A_REVERSE` if no color)
- Help overlay (`?`) skips the status bar — it draws its own centered
  title at `y=0`.

## Views

| Mode | Key | What it shows |
|---|---|---|
| **Year**   | `y` | 3×4 grid of mini months; today's month header has `COLORS["today"]` + `A_REVERSE` if cursor month == today month; each day cell renders `T` for today, day-number otherwise |
| **Month**  | `m` | Mon-Sun 6-row grid; today green+bold, weekend magenta, cursor reverse; event-marker `•` in cells with events |
| **Week**   | `w` | 7-day hourly grid (default 08:00–22:00, configurable via `TUICAL_HOUR_*`); event cells have `COLORS["block_timed_bg"]` (blue bg); cursor column reverse |
| **Day**    | `d` | Single-day hourly grid; timed events rendered as bg-colored blocks spanning their hour rows + `▎` continuation marker; all-day strip at top with `block_allday_bg` (cyan bg) |
| **Agenda** | `a` | Flat event list within today ± 30 days, sorted by start; today green, past magenta, all-day cyan |
| **Help**   | `?` | Static keybinding table (centered, auto-generated from `keymap.KEYMAP`) |

### Navigation per view

| View | `h` `l` | `j` `k` | `n` `N` |
|---|---|---|---|
| Year   | prev / next month | ±3 months | ±1 year |
| Month  | prev / next day  | ±1 week   | prev / next month |
| Week   | prev / next day  | ±1 week   | prev / next week |
| Day    | prev / next day  | ±1 hour   | prev / next day |
| Agenda | prev / next event | prev / next event | ±30 days |

`g` jumps to today; `G` jumps to end of the current period
(last day of month, last day of week, 23:00 of day, end of agenda list).

### Cursor conventions

- All views track a single `state.cursor` (a `date`) except:
  - Year uses `state.view_year + state.cursor.month` (cursor is a
    `date` but only year+month matter)
  - Week & day also use `state.view_year`/`view_month` for the header
- Movement that crosses a period boundary updates `state.view_year`
  / `view_month` accordingly.

## Visual design

| Element | Attribute |
|---|---|
| Today | green + bold (`COLORS["today"]`) |
| Weekend (Sat/Sun column) | magenta |
| All-day events | cyan |
| Cursor day/cell | reverse video (`A_REVERSE`) |
| Title text | yellow + bold |
| Footer / nav hint | dim |
| Status bar | white on blue (or `A_REVERSE` fallback) |
| Timed event block bg | black on blue (`COLORS["block_timed_bg"]`) |
| All-day block bg | black on cyan (`COLORS["block_allday_bg"]`) |
| Today marker (year view) | ASCII `T` |

### Cursor + today combo (v0.6 fix)

When cursor lands on today, the cell must show **both** `A_REVERSE` (cursor)
and `COLORS["today"]` (today). Use **OR-assignment** (`|=`), never replace (`=`):

```python
head_attr = curses.A_NORMAL
if is_cursor:
    head_attr |= curses.A_REVERSE
if is_today:
    head_attr |= COLORS["today"]
```

The v0.6 year-view bug was using `=` instead of `|=` on the today branch,
which dropped `A_REVERSE` when `cursor.month == today.month`. Caught by
`tests/test_render.py::test_year_view_today_attr_when_cursor_equals_today`.

## Rendering contract

Every view (`ui/<view>.py`) exposes:

```python
def render(stdscr, state, cfg, h: int, w: int) -> None: ...
def handle(state, key: int) -> None: ...
def event_on_cursor(state) -> Event | None: ...
```

`render` must:

- Wrap every `addnstr` / `hline` in `contextlib.suppress(curses.error)`
  (terminals raise on edge cells — noisy during resize)
- Never write to `y=0` (status bar territory) — except `help.py` which
  replaces it with its own centered title

`handle` may mutate `state.cursor`, `state.view_year`, `state.view_month`,
`state.mode` (cross-view switch). It does **not** mutate event list —
that's `form.py`'s job.

`event_on_cursor` returns the event at cursor (for `Enter`/`e`/`D`)
or `None` when the cursor has no event.
