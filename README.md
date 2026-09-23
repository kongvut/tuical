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

## v0.1 keys (month view)

`a` add · `e` edit · `d` delete · `n`/`p` next/prev month · `g` today ·
`h`/`j`/`k`/`l` or arrows to move · `q` quit
