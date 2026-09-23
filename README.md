# tuical — local terminal calendar

Single-user, local-only calendar TUI in pure Python (stdlib only).

## Run

```sh
pip install -e .
python -m tuical
```

## Storage

Events live in `~/.config/tuical/events.json` by default. Override with `TUICAL_DATA`.

## Env vars

| Var | Default | Meaning |
| --- | --- | --- |
| `TUICAL_DATA` | `~/.config/tuical/events.json` | JSON store path |
| `TUICAL_TZ` | `Asia/Bangkok` | Default timezone |
| `TUICAL_HOUR_START` | `8` | Week/day view start hour |
| `TUICAL_HOUR_END` | `22` | Week/day view end hour |
| `TUICAL_24H` | `1` | `0` for 12-hour clock |
| `NO_COLOR` | (unset) | If set, disable color |

## Keybindings

Per `SPEC.md`:

| Key | Action |
| --- | --- |
| `q` / `Ctrl-C` | quit |
| `h` `j` `k` `l` / arrows | move cursor (mode-adaptive) |
| `g` / `G` | today / end of period |
| `y` `m` `w` `d` `a` | switch view (year/month/week/day/agenda) |
| `n` / `N` | next / prev period (day/week/month/year ตาม mode) |
| `t` / `+` / `-` | today / forward 1 / back 1 |
| `e` | edit event at cursor |
| `Enter` | add event at cursor |
| `D` | delete event at cursor (confirm) |
| `/` | search (v0.5) |
| `?` | help overlay (v0.5) |
| `:` | command palette (v0.5) |

## Views implemented

- **Year** (`y`) — 3x4 grid of mini months, cursor month=reverse, today=bold
- **Month** (`m`) — 7-col Mon–Sun grid, event marker `•`, today=bold, cursor=reverse
- **Week** (`w`) — 7-day hourly grid (TUICAL_HOUR_START..TUICAL_HOUR_END), all-day strip
- **Day** (`d`) — single-day hourly grid with auto-extended range to fit late/early events
- **Agenda** (`a`) — sorted event list within today ± 30 days

## v0.5 features

- `/` search by summary (case-insensitive substring, jumps cursor to first match)
- `?` help overlay listing all keybindings (Esc/q/?/Enter to dismiss)
- `:` command palette:
  - `goto YYYY-MM-DD` — move cursor to date
  - `export <path>` — write `.ics` (RFC 5545)
  - `import <path>` — read `.ics`, merge by UID (replace existing, append new)
  - `quit` — exit

## Status

- ✅ v0.1 — month + add/edit/delete + JSON store
- ✅ v0.2 — week + day + full vim-style keybindings
- ✅ v0.3 — year + agenda
- ✅ v0.4 — .ics import/export (VEVENT, floating local time + VALUE=DATE, no VTIMEZONE/RRULE)
- ✅ v0.5 — search + help + command palette
