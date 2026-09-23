# Data model

`tuical` stores events as JSON on disk. Single calendar, single file.

## Event

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Event:
    id: str         # uuid4 hex (32 chars), or imported .ics UID
    summary: str    # non-empty (validator)
    start: datetime # naive local time
    end: datetime   # naive local time, end > start
    all_day: bool
```

### Invariants (enforced by `store.validate_event`)

- `summary.strip()` is non-empty
- `end > start`
- `start` and `end` are both naive (no tzinfo)
- All-day events store `start=00:00:00.000000` and `end=23:59:59.999999`
  on the **same day** — keeps `end > start` true while preserving the
  "all-day" semantic without a separate `duration` field. Display layer
  uses `cfg.hour_start..cfg.hour_end` for the rendering window; the
  all-day flag tells the renderer to skip the hourly grid.

## JSON envelope

```json
{
  "version": 1,
  "events": [
    {
      "id": "9f1c...32hex",
      "summary": "team standup",
      "start": "2026-09-23T09:00:00",
      "end":   "2026-09-23T09:30:00",
      "all_day": false
    }
  ]
}
```

- Top-level `version` field — bump on incompatible schema change; load
  rejects unknown versions with a clear error rather than silent migration.
- Dates/times serialized as **ISO-8601 naive local** strings. Importer must
  reject aware datetimes (we don't store TZ yet).
- File written atomically (`.tmp` + `os.replace`), guarded by `fcntl.flock`
  to prevent concurrent writers from corrupting the file.
- Before each write, the existing file is rotated to `events.json.bak`
  (single backup, one generation — sufficient for human-edited or
  crash-mid-write recovery).

## Storage path

- Default: `~/.config/tuical/events.json`
- Override: `TUICAL_DATA` env var (used by tests; `tests/` set it to
  `tmp_path / "events.json"`).

## Config (env vars)

| Var | Default | Meaning |
|---|---|---|
| `TUICAL_DATA` | `~/.config/tuical/events.json` | JSON store path |
| `TUICAL_TZ` | `Asia/Bangkok` | Display TZ (naive datetimes assumed in this zone) |
| `TUICAL_HOUR_START` | `8` | week/day view start hour (0–23) |
| `TUICAL_HOUR_END` | `22` | week/day view end hour (1–24) |
| `TUICAL_24H` | `1` | `0` = 12-hour format with AM/PM |
| `NO_COLOR` | (unset) | any non-empty value disables color init |

`Config` is built once at startup by `config.from_env()`; all views read
read-only. `use_color=False` (from `NO_COLOR` or terminal without color
support) gates `init_colors()` and views fall back to plain attrs
(`A_BOLD` / `A_DIM` / `A_REVERSE`).
