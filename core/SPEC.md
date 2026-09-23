# Overview

Personal calendar TUI. Python stdlib only — single user, single calendar,
local-only. Built to replace KDE calindori with a small fast curses app.

## Goal

- TUI calendar เบา รันทันทีทุก shell — `python -m tuical` ใน terminal จริง
- Views ครบ: **year / month / week / day / agenda**
- เพิ่ม/ลบ/แก้ event ได้ (ทั้ง all-day และ timed)
- อ่าน/เขียน `.ics` (RFC 5545) เพื่อ import/export กับแอปอื่น
- Vim-style keys + สี + status bar ที่อ่านง่าย

## Non-goals

- ❌ CalDAV / network sync
- ❌ Note / TODO / reminders / alarm daemon
- ❌ Recurrence rules (`RRULE`) — เพิ่มใน v1.0
- ❌ Multi-calendar / multi-user
- ❌ Plugin system

## Stack

- Python **3.14** (pin ผ่าน `mise.toml`)
- stdlib เท่านั้น — `curses`, `datetime`, `json`, `dataclasses`, `zoneinfo`, `collections.abc`, `pathlib`, `uuid`, `fcntl`, `tempfile`, `dataclasses`
- Build: `setuptools>=61` (dev only)
- Lint: `ruff` (rules E/F/I/W/UP/B/SIM)
- Test: `pytest` (unit + mock-stdscr render)

## Architecture

```
src/tuical/
├── __main__.py          curses.wrapper(main) entrypoint
├── app.py               main loop, state, dispatch, Esc handler
├── config.py            Config dataclass from env
├── store.py             Event dataclass + JSON load/save (atomic, flock, .bak)
├── ical.py              RFC 5545 export/import (VEVENT only)
└── ui/
    ├── common.py        COLORS dict, status_bar(), init_colors()
    ├── keymap.py        master KEYMAP — drives dispatch + help overlay
    ├── month.py week.py day.py year.py agenda.py
    └── help.py          overlay, auto-generated from keymap.KEYMAP
```

### Module responsibilities

- **`app.py`** — `main(stdscr)`: load config → init colors (gated by `cfg.use_color`) →
  load events → render → getch → dispatch (Esc writes `mode = prev_mode`,
  mode keys switch view, `?`/`/`:`:` start overlay, `Enter`/`e`/`D` start form) →
  save on quit.
- **`store.py`** — atomic JSON write via `.tmp` + `replace()`, `fcntl.flock` for
  cross-process safety, rotate `events.json.bak` on every save.
  Validator: `end > start`, `summary` non-empty.
- **`ical.py`** — VEVENT only. Floating local-time `DTSTART`/`DTEND` for timed,
  `VALUE=DATE` for all-day. VTIMEZONE / RRULE raise `ValueError("v0.4 limitation")`.
- **`ui/common.py`** — color pair init + `COLORS` module dict + `status_bar()`
  helper. Module-level so views reference without threading attrs.
- **`ui/keymap.py`** — single `KEYMAP` dict drives both dispatch and the `?`
  help overlay (no drift between code and docs).
- **`ui/<view>.py`** — every view exposes `render(stdscr, state, cfg, h, w)`,
  `handle(state, key)`, `event_on_cursor(state)`. Status bar at `y=0` is overlaid
  by `app.py`, so views don't draw their own title. Help overlay skips status bar.

## Milestones

| Tag | Status | Content |
|---|---|---|
| v0.1 | ✅ | month view + add/edit/delete + JSON store |
| v0.2 | ✅ | week + day views + full vim-style keybindings |
| v0.3 | ✅ | year view (3×4 mini) + agenda list |
| v0.4 | ✅ | .ics import/export (RFC 5545 VEVENT) |
| v0.5 | ✅ | search (`/`) + help (`?`) + palette (`:`) |
| v0.6 | ✅ | status bar, 8 color pairs, event blocks, today+cursor combo fix, Esc |
| v1.0 | 🔜 | RRULE expansion + timezone-aware datetimes |

Tagged on github: `v0.1.0` (replaced) → `v0.1.1` (current).

## Roadmap (v1.0+)

- **RRULE expansion** — add `RRULE` field to `Event`, expand in view code, full
  v0.4 `.ics` round-trip with EXDATE.
- **Timezone-aware datetimes** — shift from naive to
  `datetime[zoneinfo.ZoneInfo]`. Affects storage format (migration).
- **Search result highlighting** — `/foo` currently jumps cursor; show match
  in agenda too.
- **Multi-line description** — separate `description` field (currently single
  line in `summary`).
- **Mouse** — curses mouse events for click-to-navigate.
- **Thai year (`พ.ศ. = +543`)** — toggle in config; display alongside ISO year.
- **Lunar** — Chinese / Thai lunar dates; requires ephemeris.
- **External editor** — `$EDITOR` for multi-line event descriptions.
- **Multi-calendar** — split storage per calendar + selector in status bar.

## Open questions

1. Multi-line summary → separate `description` field, or richer `summary`?
2. Timezone-aware datetimes — naive + `TUICAL_TZ` works for one user, breaks
   for travel across zones. Worth it for v1.0?
3. Search result highlighting — `/foo` currently jumps cursor to first match.
   Should the match also be highlighted in agenda view?
4. Lunar calendar wanted? Affects year-view cell size.

## Design decisions (resolved)

| Decision | Choice | Rationale |
|---|---|---|
| Runtime deps | stdlib only | 0 install friction |
| Python version | 3.14 (mise pin) | latest stable; user env |
| Build backend | setuptools | universal; no hatchling/poetry lock-in |
| Storage format | JSON v1 envelope | human-readable, `version` field for migration |
| All-day event end | `23:59:59.999999` same day | keeps `end > start` invariant; simpler than RFC 5545 exclusive end |
| ical.py unsupported features | raise `ValueError` | fail loud instead of silently dropping data |
| Status bar overlay | overwrite view title at `y=0` | saves diff churn across every view |
| `Esc` handler | toggle `mode ← prev_mode` | exit any overlay back to previous view |
| View titles removed | views no longer draw title | status bar replaces them |
| Event block rendering | bg color via `color_pair(fg, bg)` | visible time-spans without box drawing |
| View dispatch | single `VIEWS` dict in `app.py` | one place to add new views |
| Master keymap | `ui/keymap.KEYMAP` | single source of truth for dispatch + help |

## Run / install / verify

```sh
mise install                                    # python 3.14
pip install -e .                                # editable install
python -m tuical                                # launch TUI
```

Verification:

```sh
mise exec -- ruff check src/ tests/             # must be 0 errors
mise exec -- pytest -q                          # all tests pass
mise exec -- python -m build                    # sdist + wheel
```
