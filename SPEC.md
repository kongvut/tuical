# tuical — TUI Calendar (Python)

Personal calendar TUI ใช้เอง, **local-only**, ไม่มี CalDAV/sync, ไม่มี note/reminder
ขึ้นบน Python **stdlib เท่านั้น** (`curses`, `datetime`, `json`, `dataclasses`)

## Goal

- TUI calendar เบา รันทันทีทุก shell
- Views ครบ: **year / month / week / day** + agenda list
- เพิ่ม/ลบ/แก้ event ได้ (ทั้ง all-day และ timed)
- อ่าน/เขียน `.ics` (RFC 5545) เพื่อ import/export กับแอปอื่น

## Non-goals

- ❌ CalDAV / network sync
- ❌ Note / TODO / reminders / alarm daemon
- ❌ Recurrence rules (อาจเพิ่มทีหลัง — ไม่ใช่ v0)
- ❌ Multi-calendar / multi-user
- ❌ Plugin system

## Stack

- Python 3.11+ (มีอยู่แล้วบน t14-arch)
- stdlib เท่านั้น — `curses` สำหรับ UI, `datetime` สำหรับวันที่, `json` สำหรับเก็บ event
- ไม่มี pip dependency → 0 install step
- ~600-800 LOC ทั้งโปรเจกต์ (คาด)

## Views

| Mode | Key | สิ่งที่แสดง |
|---|---|---|
| Year | `y` | 12 เดือนเรียง 3x4 (mini calendar), นำทางข้ามปีได้ |
| Month | `m` | เดือนเต็ม, วันที่มี event = มี marker |
| Week | `w` | 7 วัน, hourly grid 09:00-21:00 (configurable) |
| Day | `d` | วันเดียว, hourly grid 24 ชม. หรือ 06-22 (configurable) |
| Agenda | `a` | list event ในอนาคต + ย้อนหลัง N วัน |

ทุก mode: **วันนี้** highlighted, **selected day** มี cursor, **events** มี block แยกตาม all-day/timed

## Keybindings (vim-style + arrows)

| Key | Action |
|---|---|
| `q` / `Ctrl-C` | quit |
| `h` `j` `k` `l` / `←` `↓` `↑` `→` | move cursor (prev/next day, week, month, year ตาม mode) |
| `g` / `G` | ไปวันนี้ / ไปท้ายสุด |
| `y` / `m` / `w` / `d` / `a` | switch view |
| `n` / `N` | next/prev period (ขึ้นกับ mode — day→week→month→year) |
| `t` / `+` / `-` | today / ไปข้างหน้า 1 / ถอยหลัง 1 |
| `e` | edit event ของวันที่ cursor ชี้ |
| `Enter` | add event ที่ cursor |
| `D` | delete event (confirm) |
| `/` | search by summary text (jump to event) |
| `?` | help overlay |
| `:` | command palette (`goto`, `export`, `import`, `quit`) |

## Data model

Event:
```python
@dataclass
class Event:
    id: str         # uuid4
    summary: str    # หัวข้อ
    start: datetime # naive local time
    end: datetime   # naive local time, end > start
    all_day: bool
```

Single user, single calendar (v0). Storage = JSON file ที่ `~/.config/tuical/events.json` (override ได้ด้วย env `TUICAL_DATA`)

## File layout

```
tuical/
├── SPEC.md            # ไฟล์นี้
├── README.md          # quick start
├── pyproject.toml     # ไม่มี deps, แค่ metadata + ruff config
├── src/
│   └── tuical/
│       ├── __main__.py  # python -m tuical entrypoint
│       ├── app.py       # main loop, mode/state machine
│       ├── ui/
│       │   ├── year.py
│       │   ├── month.py
│       │   ├── week.py
│       │   ├── day.py
│       │   └── agenda.py
│       ├── store.py     # JSON load/save
│       ├── ical.py      # .ics import/export (stdlib-only)
│       └── config.py    # defaults, env vars
└── tests/
    └── test_store.py
```

## Config (env vars, optional)

| Var | Default | Purpose |
|---|---|---|
| `TUICAL_DATA` | `~/.config/tuical/events.json` | path to JSON store |
| `TUICAL_TZ` | `Asia/Bangkok` | default timezone (naive datetimes ตีความเป็น TZ นี้) |
| `TUICAL_HOUR_START` | `8` | week/day view start hour |
| `TUICAL_HOUR_END` | `22` | week/day view end hour |
| `TUICAL_24H` | `1` | `0` = 12h format |
| `NO_COLOR` | (off) | respect for stripes/boxes |

## Milestones (proposed)

- [ ] **v0.1** — month view + add/edit/delete events + JSON store
- [ ] **v0.2** — week view + day view + keybindings ครบ
- [ ] **v0.3** — year view + agenda
- [ ] **v0.4** — .ics import/export
- [ ] **v0.5** — search + help overlay + command palette

## Decisions to revisit (open)

1. **Color**: ใช้สี default terminal + dim for non-current days, หรืออยาก custom palette?
   → เริ่ม default + override via env ก่อน
2. **Timezone storage**: `datetime` naive (assume `TUICAL_TZ`) vs aware (with `zoneinfo`)
   → ใช้ naive + assume TZ เดียวใน v0, aware ใน v0.5 ถ้าจำเป็น
3. **.ics export scope**: ทั้งหมด vs ช่วงวันที่เลือก — ตัดสินตอน v0.4
4. **Recurrence rules** — ใส่ใน v1.x หรือก่อน? (ตอนนี้ถือว่าทุก event = single occurrence)
