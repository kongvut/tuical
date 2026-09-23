# tuical — local TUI calendar

Personal calendar TUI written in Python stdlib only (no runtime deps).
Local-only, single user, single calendar. Built to replace Qt/KDE calindori
with a small fast curses app.

## Goal

- TUI calendar เบา รันทันทีทุก shell — `python -m tuical` ใน terminal จริง
- Views ครบ: **year / month / week / day / agenda**
- เพิ่ม/ลบ/แก้ event ได้ (ทั้ง all-day และ timed)
- อ่าน/เขียน `.ics` (RFC 5545) เพื่อ import/export กับแอปอื่น
- Vim-style keys + สี + status bar ที่อ่านง่าย

## Non-goals

- ❌ CalDAV / network sync
- ❌ Note / TODO / reminders / alarm daemon
- ❌ Recurrence rules (`RRULE`) — เพิ่มใน v1.x เมื่อมี RFC 5545 expansion
- ❌ Multi-calendar / multi-user
- ❌ Plugin system

## Stack

- Python **3.14** (pin ผ่าน `mise.toml`)
- stdlib เท่านั้น — `curses`, `datetime`, `json`, `dataclasses`, `zoneinfo`, `collections.abc`, `pathlib`, `uuid`
- Build: `setuptools>=61` (dev only — ไม่ใช่ runtime dep)
- Lint: `ruff` (rules E/F/I/W/UP/B/SIM)
- Test: `pytest` (52 tests, ไม่มี UI tests — render ต้องใช้ terminal จริง)
- Total ~2,200 LOC

## Architecture

```
tuical/
├── SPEC.md
├── README.md
├── pyproject.toml           # metadata + ruff config; license = "MIT" (SPDX)
├── mise.toml                # python = "3.14" pin
├── .lsp.json                # pylsp config
├── .gitignore
└── src/tuical/
    ├── __init__.py
    ├── __main__.py          # curses.wrapper(main) entrypoint
    ├── app.py               # main loop, mode/state machine, Esc handler
    ├── config.py            # Config dataclass from env
    ├── store.py             # Event dataclass + JSON load/save (atomic)
    ├── ical.py              # RFC 5545 export/import (VEVENT only)
    └── ui/
        ├── common.py        # COLORS dict, status_bar helper, date helpers
        ├── month.py         # Mon-Sun 6-row grid
        ├── week.py          # 7-day hourly grid + event-cell bg
        ├── day.py           # single-day hourly grid + event blocks
        ├── year.py          # 3x4 mini months + today marker
        ├── agenda.py        # flat list ± 30 days
        └── help.py          # static keybinding table
```

### Module responsibilities

- **`app.py`** — `main(stdscr)` orchestrates curses loop: load config → init colors
  → load events → render → getch → dispatch (Esc toggles prev view, mode keys
  switch view, Enter/e/D start form, ?/`/`:` start overlay) → save on quit.
- **`store.py`** — atomic JSON write via `.tmp` + `replace`; all-day events stored
  with `start=00:00:00`, `end=23:59:59.999999` same day. Validator: end > start,
  summary non-empty.
- **`ical.py`** — VEVENT only. Floating local-time DTSTART/DTEND for timed,
  `VALUE=DATE` for all-day. VTIMEZONE / RRULE raise `ValueError("v0.4 limitation")`.
- **`ui/common.py`** — color pair init + status_bar builder. Module-level `COLORS`
  dict so views reference without threading attrs through signatures.
- **`ui/<view>.py`** — each view exposes `render(stdscr, state, cfg, h, w)`,
  `handle(state, key)`, `event_on_cursor(state)`. Status bar at y=0 overlaid
  by `app.py`, so views don't render their own title (except help, which skips
  status bar).

## Data model

```python
@dataclass
class Event:
    id: str         # uuid4 hex (32 chars), or imported .ics UID
    summary: str    # non-empty
    start: datetime # naive local time
    end: datetime   # naive local time, end > start
    all_day: bool
```

JSON envelope: `{"version": 1, "events": [...]}`. Atomic write via temp file +
`replace()`. Path from `TUICAL_DATA` env var (default
`~/.config/tuical/events.json`).

## Views

| Mode | Key | What it shows |
|---|---|---|
| Year   | `y` | 3x4 grid of mini months; today marked with `T` and green month header |
| Month  | `m` | Mon–Sun 6-row grid; events marker `•`; today green+bold, weekend magenta, cursor reverse |
| Week   | `w` | 7-day hourly grid (default 08–22); event cells have bg color; cursor column reverse |
| Day    | `d` | Single-day hourly grid; events as bg-colored blocks spanning their hour rows; all-day strip |
| Agenda | `a` | Flat event list within today ± 30 days, sorted by start; today green, past magenta, all-day cyan |
| Help   | `?` | Static keybinding table; dismiss with Esc/q/?/Enter |

All views share a unified top status bar (line 0):
```
  [ MONTH]  Wed 23 Sep 2026  ·  cursor 2026-09-23  ·  5 event(s)
```
white-on-blue bg (or `A_REVERSE` fallback).

## Keybindings

| Key | Action |
|---|---|
| `q` / `Ctrl-C` | quit |
| `Esc` | go back to previous view (toggle) |
| `h` `j` `k` `l` / `←` `↓` `↑` `→` | move cursor (mode-adaptive) |
| `g` / `G` | today / end of period |
| `y` `m` `w` `d` `a` | switch view (lowercase only) |
| `n` / `N` | next / prev period |
| `t` / `+` / `-` | today / forward 1 / back 1 |
| `Enter` | add event at cursor |
| `e` | edit event at cursor |
| `D` (shift) | delete event at cursor (confirm) |
| `/` | search by summary (case-insensitive substring, jump cursor) |
| `?` | help overlay |
| `:` | command palette: `goto YYYY-MM-DD`, `export <path>`, `import <path>`, `quit` |

Note: SPEC table is lowercase-only for view-switch keys. Pressing `Y` does nothing.

## Visual design

| Element | Attribute |
|---|---|
| Today | green + bold |
| Weekend (Sat/Sun column) | magenta |
| All-day events | cyan |
| Cursor day/cell | reverse video (overrides other attrs but preserved via OR) |
| Title text | yellow + bold |
| Footer hints | dim |
| Status bar | white on blue (or `A_REVERSE` fallback) |
| Timed event block bg | black on blue |
| All-day block bg | black on cyan |
| Today marker (year view mini cells) | ASCII `T` |

`NO_COLOR=1` users get plain attrs (A_BOLD / A_DIM / A_REVERSE) — `cfg.use_color`
gates `init_colors()` call.

## Config (env vars)

| Var | Default | Meaning |
|---|---|---|
| `TUICAL_DATA` | `~/.config/tuical/events.json` | JSON store path |
| `TUICAL_TZ` | `Asia/Bangkok` | Display TZ (naive datetimes assume this) |
| `TUICAL_HOUR_START` | `8` | week/day view start hour |
| `TUICAL_HOUR_END` | `22` | week/day view end hour |
| `TUICAL_24H` | `1` | `0` = 12h format |
| `NO_COLOR` | (unset) | disable color init |

## Milestones

- ✅ **v0.1** — month view + add/edit/delete events + JSON store
- ✅ **v0.2** — week + day views + full vim-style keybindings
- ✅ **v0.3** — year view (3x4 mini) + agenda list
- ✅ **v0.4** — `.ics` import/export (RFC 5545 VEVENT, floating local time + VALUE=DATE)
- ✅ **v0.5** — search (`/`) + help overlay (`?`) + command palette (`:`)
- ✅ **v0.6** — UI polish: top status bar, color pairs (today/weekend/allday),
  event blocks in day view, bg color on week event cells, today+cursor combo fix,
  Esc handler to toggle back to previous view, `__main__.py` `curses.wrapper`
  launch fix (v0.1.0/v0.1.1 was technically unrunnable in TTY)

Tagged releases on github: `v0.1.0` (replaced) → `v0.1.1` (current).

## Run / install / verify

```sh
mise install                                    # python 3.14
pip install -e .                                # editable install
python -m tuical                                # launch TUI
```

Verification:
```sh
mise exec -- ruff check src/ tests/             # must be 0 errors
PYTHONPATH=src mise exec -- pytest tests/ -q    # 52/52 must pass
PYTHONPATH=src mise exec -- python -m build     # sdist + wheel
```

## Roadmap (v1.x candidates)

Per SPEC "open decisions" + user-stated needs:

| Feature | Notes |
|---|---|
| Recurrence (`RRULE`) | expand v0.4 ical.py — storage layer needs RRULE field + expansion logic |
| `TZID` / timezone-aware datetimes | shift from naive to `datetime[zoneinfo.ZoneInfo]`; affects storage format |
| Attachments / file refs | per-event URI or local path |
| Multi-calendar | split storage per calendar + selector in status bar |
| Mouse support | curses mouse events for click-to-navigate; minor |
| Thai year display (พ.ศ. = +543) | toggle in config; display alongside ISO year |
| Lunar calendar overlay | Chinese / Thai lunar dates; non-trivial, requires ephemeris |
| External editor for summary | `$EDITOR` for multi-line event descriptions (currently single-line) |
| Search highlighting | `/` matches shown in agenda and list views, not just cursor jump |
| Recurring event exceptions | `EXDATE` in ical.py + override list in Event |

## Design decisions (resolved)

| Decision | Choice | Rationale |
|---|---|---|
| Runtime deps | stdlib only | SPEC requires no install; 0 friction |
| Python version | 3.14 (mise pin) | latest stable, matches user's mise env |
| Build backend | setuptools | universal; no hatchling/poetry lock-in |
| Storage format | JSON v1 envelope | human-readable, easy to debug, version field for migration |
| All-day event end | `23:59:59.999999` same day | keeps `end > start` invariant; simpler than RFC 5545 exclusive end |
| ical.py unsupported features | raise `ValueError` | fail loud instead of silently dropping data |
| Status bar overlay | overwrite view title at y=0 | saves diff churn across every view |
| `Esc` handler | toggle between current and prev_mode | user-friendly exit from any view |
| View titles removed | views no longer draw title | status bar replaces them; cleaner code |
| Event block rendering | bg color via `color_pair(fg, bg)` | visible time-spans in day view without box drawing |
| All view dispatch | single `VIEWS` dict in `app.py` | one place to add new views |

## Open questions

1. **Multi-line summary** — currently single-line. Spec a separate `description` field?
2. **Timezone-aware datetimes** — naive + `TUICAL_TZ` works for one user, breaks
   for travel across zones. Worth it for v1?
3. **Search result highlighting** — `/foo` currently jumps cursor to first match.
   Should the match also be highlighted in agenda view?
4. **Lunar calendar** — is Thai lunar (`ปฏิทินจันทรคติ`) wanted? Affects year view size.
