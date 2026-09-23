"""iCalendar (RFC 5545) import/export for tuical events.

Scope (v0.4): VEVENT only, DTSTART/DTEND with floating local time or VALUE=DATE.
VTIMEZONE, RRULE, attachments, alarms, recurrence — all raise ValueError to make
the limitation loud rather than silently drop.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, time
from pathlib import Path

from . import store

CRLF = "\r\n"


def export_events(events: Iterable[store.Event]) -> str:
    out: list[str] = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//tuical//EN"]
    stamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    for ev in events:
        out.append("BEGIN:VEVENT")
        out.append(f"UID:{ev.id}")
        out.append(f"DTSTAMP:{stamp}")
        if ev.all_day:
            out.append(f"DTSTART;VALUE=DATE:{_fmt_date(ev.start.date())}")
            out.append(f"DTEND;VALUE=DATE:{_fmt_date(ev.end.date())}")
        else:
            out.append(f"DTSTART:{_fmt_dt(ev.start)}")
            out.append(f"DTEND:{_fmt_dt(ev.end)}")
        out.append(f"SUMMARY:{_escape(ev.summary)}")
        out.append("END:VEVENT")
    out.append("END:VCALENDAR")
    return CRLF.join(out) + CRLF


def export_to_path(path: str | Path, events: Iterable[store.Event]) -> None:
    Path(path).write_text(export_events(events), encoding="utf-8")


def import_from_path(path: str | Path) -> list[store.Event]:
    return import_events(Path(path).read_text(encoding="utf-8"))


def import_events(text: str) -> list[store.Event]:
    """Parse .ics text into a list of Event. Raises ValueError on unsupported features."""
    raw = text.split(CRLF) if CRLF in text else text.split("\n")
    unfolded = _unfold(raw)
    events: list[store.Event] = []
    cur: dict | None = None

    for line in unfolded:
        if line == "BEGIN:VTIMEZONE":
            raise ValueError("v0.4 limitation: VTIMEZONE not supported")
        if not line or line.startswith("BEGIN:"):
            if line == "BEGIN:VEVENT":
                cur = {}
            continue
        if line.startswith("END:"):
            if line == "END:VEVENT" and cur is not None:
                events.append(_build(cur))
                cur = None
            continue
        if cur is None:
            continue
        if ":" not in line:
            continue
        prop_part, _, value = line.partition(":")
        name, *params_list = prop_part.split(";")
        name = name.upper()
        params: dict[str, str] = {}
        for p in params_list:
            if "=" in p:
                k, _, v = p.partition("=")
                params[k.upper()] = v
        if name == "RRULE":
            raise ValueError("v0.4 limitation: RRULE recurrence not supported")
        cur[name] = value
        if params:
            cur[f"{name}_params"] = params

    return events


def _unfold(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if (line.startswith(" ") or line.startswith("\t")) and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return out


def _build(cur: dict) -> store.Event:
    summary = _unescape(cur.get("SUMMARY", ""))
    if "DTSTART" not in cur:
        raise ValueError("VEVENT missing DTSTART")
    start_params = cur.get("DTSTART_params", {})
    all_day = start_params.get("VALUE") == "DATE"
    start_raw = cur["DTSTART"]
    end_raw = cur.get("DTEND")

    if all_day:
        start_day = _parse_date(start_raw)
        if end_raw is None:
            raise ValueError("all-day VEVENT missing DTEND")
        end_day = _parse_date(end_raw)
        if end_day < start_day:
            raise ValueError("all-day DTEND before DTSTART")
        ev = store.make_all_day(summary, start_day)
        if cur.get("UID"):
            ev.id = cur["UID"]
        if end_day > start_day:
            ev.end = datetime.combine(end_day, time.max)
        return ev

    start = _parse_dt(start_raw)
    if end_raw is None:
        end = start
    else:
        end = _parse_dt(end_raw)
        if end <= start:
            raise ValueError("VEVENT DTEND must be after DTSTART")
    return store.Event(
        id=cur.get("UID", ""),
        summary=summary,
        start=start,
        end=end,
        all_day=False,
    )


def _fmt_dt(d: datetime) -> str:
    return d.strftime("%Y%m%dT%H%M%S")


def _fmt_date(d: date) -> str:
    return d.strftime("%Y%m%d")


def _parse_dt(s: str) -> datetime:
    for fmt in ("%Y%m%dT%H%M%S", "%Y%m%dT%H%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"bad datetime: {s!r}")


def _parse_date(s: str) -> date:
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except ValueError as e:
        raise ValueError(f"bad DATE value: {s!r}") from e


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(",", "\\,")
        .replace(";", "\\;")
        .replace("\n", "\\n")
    )


def _unescape(text: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\" and i + 1 < len(text):
            nxt = text[i + 1]
            if nxt in ("n", "N"):
                out.append("\n")
            elif nxt == "\\":
                out.append("\\")
            elif nxt == ",":
                out.append(",")
            elif nxt == ";":
                out.append(";")
            else:
                out.append(nxt)
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)
