# Events — add / edit / delete

Events are the only mutable user-data. Add, edit, delete flow through
a single in-terminal form (`ui/form.py`), with no external editor in
v0.x.

## Triggers

| Key | Action |
|---|---|
| `Enter` | **add** event at cursor (timestamp preset to cursor's date + nearest hour) |
| `e` | **edit** event under cursor (if any — `event_on_cursor(state)`) |
| `D` (shift-d) | **delete** event under cursor (with confirm prompt) |

`Enter` adds a new event even if cursor already has one (different id).
`e` requires an event at cursor; no-op otherwise.
`D` requires an event at cursor and opens a confirm line first.

## Form fields

| Field | Type | Validation | Default on add |
|---|---|---|---|
| Summary | str | non-empty after strip | "new event" |
| Start (YYYY-MM-DD HH:MM) | str → datetime | parseable; `< end` | cursor date + `:00` |
| End (YYYY-MM-DD HH:MM)   | str → datetime | parseable; `> start` | start + 1 hour |
| All-day | bool | — | false |

Field-by-field tab navigation (`Tab` / `Shift-Tab` / arrow keys).
Submit on `Enter` from the last field or via explicit "Save" button at
bottom of form. Cancel on `Esc`.

### All-day handling

- Form sets `all_day=true` if user toggled the checkbox (single key,
  usually `a` inside form — not to be confused with `a` outside which
  opens agenda view).
- Storage writes `start=00:00:00` and `end=23:59:59.999999` of the same
  chosen day (end > start invariant preserved).
- Display layer skips hourly grid for all-day events; renders them in
  the all-day strip with cyan bg.

### Edit mode

- Pre-fills all fields from the existing event's values
- Submit overwrites the same `Event.id` (preserved through edit)
- Cancel leaves the original untouched

### Delete

- `D` from any view that has an event under cursor
- Opens a confirm prompt: `Delete "<summary>"? (y/N)`
- `y` removes the event from `state.events` + writes to disk immediately
- Any other key cancels (silent — no status message)

## Save semantics

- Add/edit → on form submit, the `Event` is appended to `state.events`
  in-memory **and** written to disk via `store.save(state.events, path)`
  (atomic + flock). No "save on quit only" — every mutation persists
  immediately. If the write fails, the in-memory event is rolled back
  and a status message shown.
- Delete → same: remove + save atomically.

## Validator

```python
def validate_event(ev: Event) -> None:
    if not ev.summary.strip():
        raise ValueError("summary must be non-empty")
    if ev.start.tzinfo is not None or ev.end.tzinfo is not None:
        raise ValueError("start/end must be naive (no tzinfo)")
    if ev.end <= ev.start:
        raise ValueError("end must be > start")
```

Called by `store.add_event`, `store.replace_event`, and the form layer
before committing.

## Import from `.ics` (delegated to `features/ics.md`)

`importer` returns a list of `Event` with **new UUIDs** to avoid id
collision with existing events. Caller decides whether to merge or
replace. Importer rejects `.ics` files containing RRULE / VTIMEZONE
(see `features/ics.md`).
