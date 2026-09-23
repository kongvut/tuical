# `.ics` import / export (RFC 5545)

RFC 5545 reader/writer for VEVENT. Implemented in `src/tuical/ical.py`.

## Scope (v0.4 / current)

Supported:

- `VEVENT` (single event or many per file)
- `SUMMARY` (UTF-8)
- `DTSTART` / `DTEND` — **floating local time** (no `TZID`)
- `DTSTART;VALUE=DATE` / `DTEND;VALUE=DATE` — all-day events
- `UID` — used as `Event.id` (else generate uuid4 hex)
- `DTSTAMP`, `CREATED`, `LAST-MODIFIED` — round-tripped as opaque `extra`
  dict (we don't read them, only preserve for export)

**Not supported in v0.x** (raise `ValueError("v0.4 limitation")` on
encounter to fail loud):

- `RRULE` / `EXDATE` / `RDATE` — recurrence
- `VTIMEZONE` / `TZID` — timezone-aware datetimes (we're naive +
  `TUICAL_TZ` only)
- `ATTACH`, `ATTENDEE`, `ORGANIZER`, `DESCRIPTION`, `LOCATION` —
  dropped silently (they're optional and we only store `summary`)

Rationale for fail-loud on RRULE/VTIMEZONE: silently dropping them
would corrupt user data on round-trip. Better to refuse and tell the
user to fix the source calendar.

## Export

```python
to_ics(events: list[Event]) -> bytes
```

- Returns RFC 5545-compliant bytes (UTF-8, CRLF line endings)
- Begins with `BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//tuical//EN\r\n`
- One `VEVENT` per event:
  - All-day: `DTSTART;VALUE=DATE:YYYYMMDD\r\n` + `DTEND;VALUE=DATE:YYYYMMDD\r\n`
    (DTEND is **inclusive** per RFC 5545 — we store
    `23:59:59.999999` but write `end.date() + 1` so the all-day day is
    preserved on round-trip)
  - Timed: `DTSTART:YYYYMMDDTHHMMSS\r\n` + `DTEND:YYYYMMDDTHHMMSS\r\n`
    (no `TZID` — floating local time, matches how we store)
- Ends with `END:VCALENDAR\r\n`
- Empty event list returns a valid empty calendar (no `VEVENT` blocks).

User trigger: `:` → `export <path>` in command palette. Overwrites
the file (atomic via `store`).

## Import

```python
from_ics(data: bytes) -> list[Event]
```

- Parses `VCALENDAR` → list of `VEVENT`
- For each `VEVENT`:
  - Read `UID` if present (else `uuid4().hex`)
  - Read `SUMMARY` (else raise — summary required)
  - Read `DTSTART`:
    - with `VALUE=DATE` → all-day, set `all_day=true`
    - bare `DTSTART` → timed, `all_day=false`
  - Read `DTEND` if present, else default to `DTSTART + 1 hour`
    (timed) or `DTSTART + 1 day` (all-day). All-day `DTEND` in RFC
    5545 is exclusive — we normalize to `DTEND - 1 day` so our
    inclusive `23:59:59.999999` storage matches.
- Reject `RRULE`, `EXDATE`, `VTIMEZONE`, `TZID` with
  `ValueError("v0.4 limitation")`. We fail-fast on the whole file —
  no partial import.

User trigger: `:` → `import <path>` in command palette. Imported
events get **new UUIDs** if their `UID` collides with an existing
event (avoids silent overwrite). Otherwise original `UID` preserved.

## Round-trip guarantees

For events that meet the v0.4 subset:

- Export `→` Import `→` Export is **byte-identical**
- Import `→` Export is **byte-identical** (modulo `DTSTAMP` which is
  the only field we don't strictly preserve)
- Imported events display correctly in all 5 views

## Known limitations (to address in v1.0)

- Recurring events (`RRULE`) collapse to a single occurrence
- Events with `TZID` are rejected (user must convert to floating local
  time before importing)
- Multi-line `SUMMARY` truncated to single line on import
- `DESCRIPTION`, `LOCATION`, `ATTENDEE` are silently dropped (not stored)
