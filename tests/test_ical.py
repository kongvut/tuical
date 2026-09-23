"""Tests for v0.4 .ics import/export round-trip."""

from __future__ import annotations

from datetime import date, datetime

from tuical import ical, store


def test_export_minimal_vcalendar_envelope():
    text = ical.export_events([])
    assert text.startswith("BEGIN:VCALENDAR\r\n")
    assert "VERSION:2.0" in text
    assert text.rstrip("\r\n").endswith("END:VCALENDAR")


def test_export_timed_event_uses_floating_local_time():
    ev = store.make_event("mtg", datetime(2026, 9, 23, 9, 30), datetime(2026, 9, 23, 10, 0))
    text = ical.export_events([ev])
    assert "DTSTART:20260923T093000" in text
    assert "DTEND:20260923T100000" in text
    assert "SUMMARY:mtg" in text
    assert f"UID:{ev.id}" in text


def test_export_all_day_event_uses_value_date():
    ev = store.make_all_day("holiday", date(2026, 4, 13))
    text = ical.export_events([ev])
    assert "DTSTART;VALUE=DATE:20260413" in text
    assert "DTEND;VALUE=DATE:20260413" in text
    assert "SUMMARY:holiday" in text


def test_export_escapes_special_chars_in_summary():
    ev = store.make_event("hi, there; bye\\now", datetime(2026, 1, 1, 9, 0))
    text = ical.export_events([ev])
    assert "SUMMARY:hi\\, there\\; bye\\\\now" in text


def test_roundtrip_timed_event_lossless():
    ev = store.make_event("standup", datetime(2026, 9, 23, 9, 30), datetime(2026, 9, 23, 10, 0))
    text = ical.export_events([ev])
    loaded = ical.import_events(text)
    assert len(loaded) == 1
    out = loaded[0]
    assert out.id == ev.id
    assert out.summary == ev.summary
    assert out.start == ev.start
    assert out.end == ev.end
    assert out.all_day is False


def test_roundtrip_all_day_event_lossless():
    ev = store.make_all_day("songkran", date(2026, 4, 13))
    text = ical.export_events([ev])
    loaded = ical.import_events(text)
    assert len(loaded) == 1
    out = loaded[0]
    assert out.id == ev.id
    assert out.summary == ev.summary
    assert out.start.date() == date(2026, 4, 13)
    assert out.all_day is True


def test_roundtrip_mixed_batch():
    events = [
        store.make_all_day("holiday", date(2026, 4, 13)),
        store.make_event("standup", datetime(2026, 4, 14, 9, 0), datetime(2026, 4, 14, 9, 30)),
        store.make_event("design", datetime(2026, 4, 14, 14, 0), datetime(2026, 4, 14, 16, 0)),
    ]
    text = ical.export_events(events)
    loaded = ical.import_events(text)
    assert len(loaded) == 3
    assert {e.summary for e in loaded} == {"holiday", "standup", "design"}
    assert sum(1 for e in loaded if e.all_day) == 1


def test_import_unfolds_long_lines():
    folded = (
        "BEGIN:VCALENDAR\r\n"
        "BEGIN:VEVENT\r\n"
        "UID:abc\r\n"
        "DTSTAMP:20260923T120000Z\r\n"
        "DTSTART:20260101T090000\r\n"
        "DTEND:20260101T100000\r\n"
        "SUMMARY:long sum\r\n"
        " mary that spans two lines\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    loaded = ical.import_events(folded)
    assert loaded[0].summary == "long summary that spans two lines"


def test_import_unescapes_special_chars():
    raw = (
        "BEGIN:VCALENDAR\r\n"
        "BEGIN:VEVENT\r\n"
        "UID:abc\r\n"
        "DTSTAMP:20260923T120000Z\r\n"
        "DTSTART:20260101T090000\r\n"
        "DTEND:20260101T100000\r\n"
        "SUMMARY:hi\\, there\\; bye\\\\now\\nnext\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    loaded = ical.import_events(raw)
    assert loaded[0].summary == "hi, there; bye\\now\nnext"


def test_import_raises_on_rrule():
    raw = (
        "BEGIN:VCALENDAR\r\n"
        "BEGIN:VEVENT\r\n"
        "UID:abc\r\n"
        "DTSTAMP:20260923T120000Z\r\n"
        "DTSTART:20260101T090000\r\n"
        "DTEND:20260101T100000\r\n"
        "SUMMARY:r\r\n"
        "RRULE:FREQ=DAILY\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    try:
        ical.import_events(raw)
    except ValueError as e:
        assert "v0.4 limitation" in str(e) and "RRULE" in str(e)
        return
    raise AssertionError("expected ValueError")


def test_import_raises_on_vtimezone():
    raw = (
        "BEGIN:VCALENDAR\r\n"
        "BEGIN:VTIMEZONE\r\n"
        "TZID:Asia/Bangkok\r\n"
        "END:VTIMEZONE\r\n"
        "BEGIN:VEVENT\r\n"
        "UID:abc\r\n"
        "DTSTAMP:20260923T120000Z\r\n"
        "DTSTART;TZID=Asia/Bangkok:20260101T090000\r\n"
        "DTEND;TZID=Asia/Bangkok:20260101T100000\r\n"
        "SUMMARY:t\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    try:
        ical.import_events(raw)
    except ValueError as e:
        assert "v0.4 limitation" in str(e)
        return
    raise AssertionError("expected ValueError")


def test_import_handles_lf_only():
    # Some exporters use LF instead of CRLF
    text = (
        "BEGIN:VCALENDAR\n"
        "BEGIN:VEVENT\n"
        "UID:abc\n"
        "DTSTAMP:20260923T120000Z\n"
        "DTSTART:20260101T090000\n"
        "DTEND:20260101T100000\n"
        "SUMMARY:x\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    ).replace("\n", "\n")
    loaded = ical.import_events(text)
    assert len(loaded) == 1
    assert loaded[0].summary == "x"
