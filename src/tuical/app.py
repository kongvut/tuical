"""Main curses loop and state machine."""

from __future__ import annotations

import contextlib
import curses
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from . import config as cfg_mod
from . import store
from .ui import day as day_view
from .ui import month as month_view
from .ui import week as week_view

VIEWS = {
    "month": month_view,
    "week": week_view,
    "day": day_view,
}


@dataclass
class Form:
    action: str  # "add" | "edit" | "delete"
    target: store.Event | None = None
    fields: list[tuple[str, str]] = field(default_factory=list)
    idx: int = 0
    buf: str = ""
    draft_summary: str = ""
    draft_start: datetime | None = None
    draft_all_day: bool = False


@dataclass
class State:
    events: list[store.Event] = field(default_factory=list)
    view_year: int = 0
    view_month: int = 0
    cursor: date = field(default_factory=date.today)
    mode: str = "month"
    prev_mode: str = "month"
    pending_key: int | None = None
    form: Form | None = None
    status: str = ""
    quit: bool = False

    def __post_init__(self) -> None:
        if self.view_year == 0:
            self.view_year = self.cursor.year
        if self.view_month == 0:
            self.view_month = self.cursor.month


def main(stdscr) -> None:
    cfg = cfg_mod.Config.load()
    state = State(events=store.load(cfg.data_path))
    with contextlib.suppress(curses.error):
        curses.curs_set(0)
    stdscr.keypad(True)

    while not state.quit:
        render(stdscr, state, cfg)
        key = stdscr.getch()
        if state.mode == "input":
            handle_input(state, key)
            continue

        if key in (ord("q"), 3):  # q or Ctrl-C
            state.quit = True
        elif key in (ord("y"), ord("m"), ord("w"), ord("d")):
            new_mode = {"y": "year", "m": "month", "w": "week", "d": "day"}[chr(key)]
            if new_mode == "year":
                state.status = "year view: v0.3"
                continue
            state.mode = new_mode
        elif key == ord("a"):
            state.status = "agenda view: v0.3"
        elif key in (10, 13, curses.KEY_ENTER):
            start_form(state, "add")
        elif key == ord("e"):
            start_form(state, "edit")
        elif key == ord("D"):
            start_form(state, "delete")
        elif key == ord("?"):
            state.status = "help: v0.5 (keys listed in status bar)"
        elif key == ord("/"):
            state.status = "search: v0.5"
        elif key == ord(":"):
            state.status = "command palette: v0.5"
        elif state.mode in VIEWS:
            VIEWS[state.mode].handle(state, key)

    store.save(cfg.data_path, state.events)


def render(stdscr, state: State, cfg: cfg_mod.Config) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    if state.mode in VIEWS:
        VIEWS[state.mode].render(stdscr, state, cfg, h, w)
    if state.mode == "input" and state.form is not None:
        prompt = f"{state.form.fields[state.form.idx][0]}{state.form.buf}"
        with contextlib.suppress(curses.error):
            stdscr.addnstr(h - 2, 0, prompt[: w - 1], w - 1, curses.A_REVERSE)
    if state.status:
        with contextlib.suppress(curses.error):
            stdscr.addnstr(h - 1, 0, f" {state.status[: w - 2]}", w - 1, curses.A_REVERSE)
    stdscr.refresh()


def start_form(state: State, action: str) -> None:
    state.prev_mode = state.mode
    if action == "add":
        start_default = f"{state.cursor.isoformat()} 09:00"
        state.form = Form(
            action="add",
            fields=[
                ("Summary: ", ""),
                ("Start [YYYY-MM-DD HH:MM | date | blank=all-day]: ", start_default),
                ("End   [YYYY-MM-DD HH:MM | blank=+1h]: ", ""),
            ],
        )
    elif action == "edit":
        ev = _event_on_cursor(state)
        if ev is None:
            state.status = "no event on cursor day"
            return
        start_str = (
            ev.start.date().isoformat() if ev.all_day else ev.start.isoformat(timespec="minutes")
        )
        end_str = "" if ev.all_day else ev.end.isoformat(timespec="minutes")
        state.form = Form(
            action="edit",
            target=ev,
            fields=[
                ("Summary: ", ev.summary),
                ("Start: ", start_str),
                ("End:   ", end_str),
            ],
        )
    elif action == "delete":
        ev = _event_on_cursor(state)
        if ev is None:
            state.status = "no event on cursor day"
            return
        state.form = Form(
            action="delete",
            target=ev,
            fields=[(f"Delete '{ev.summary}'? [y/N]: ", "")],
        )
    state.mode = "input"


def _event_on_cursor(state: State) -> store.Event | None:
    if state.mode in VIEWS:
        return VIEWS[state.mode].event_on_cursor(state)
    return None


def handle_input(state: State, key: int) -> None:
    form = state.form
    assert form is not None
    if key == 27:
        state.mode = state.prev_mode
        state.form = None
        state.status = "cancelled"
        return
    if key in (curses.KEY_BACKSPACE, 127, 8):
        form.buf = form.buf[:-1]
        return
    if key in (10, 13, curses.KEY_ENTER):
        commit_form(state)
        return
    if 32 <= key <= 126:
        with contextlib.suppress(ValueError):
            form.buf += chr(key)


def commit_form(state: State) -> None:
    form = state.form
    assert form is not None
    label, default = form.fields[form.idx]
    value = form.buf.strip() or default

    if form.action == "delete":
        if value.lower().startswith("y"):
            state.events = [e for e in state.events if e.id != form.target.id]
            state.status = "deleted"
        else:
            state.status = "delete cancelled"
        state.mode = state.prev_mode
        state.form = None
        return

    if form.idx == 0:
        if not value.strip():
            state.status = "summary required"
            return
        form.draft_summary = value.strip()
        form.idx += 1
        form.buf = ""
        return

    if form.idx == 1:
        parsed = parse_start(value, default_cursor=state.cursor)
        if parsed is None:
            state.status = f"bad start: {value!r}"
            return
        form.draft_start, form.draft_all_day = parsed
        if form.action == "edit" and not form.draft_all_day:
            form.fields[2] = (
                "End:   ",
                form.draft_start.replace(minute=form.draft_start.minute).isoformat(timespec="minutes"),
            )
        form.idx += 1
        form.buf = ""
        return

    if form.idx == 2:
        if form.draft_all_day:
            new_event = store.make_all_day(form.draft_summary, form.draft_start.date())
        else:
            end_dt: datetime | None
            if not value:
                end_dt = form.draft_start + timedelta(hours=1)
            else:
                end_dt = parse_dt(value)
                if end_dt is None:
                    state.status = f"bad end: {value!r}"
                    return
            if end_dt <= form.draft_start:
                state.status = "end must be after start"
                return
            new_event = store.make_event(form.draft_summary, form.draft_start, end_dt)

        if form.action == "add":
            state.events.append(new_event)
            state.status = f"added: {new_event.summary}"
        else:
            assert form.target is not None
            form.target.summary = new_event.summary
            form.target.start = new_event.start
            form.target.end = new_event.end
            form.target.all_day = new_event.all_day
            state.status = f"updated: {new_event.summary}"
        state.mode = state.prev_mode
        state.form = None


def parse_start(s: str, default_cursor: date) -> tuple[datetime, bool] | None:
    s = s.strip()
    if not s:
        return datetime.combine(default_cursor, time.min), True
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
        except ValueError:
            continue
        if fmt == "%Y-%m-%d":
            return datetime.combine(dt.date(), time.min), True
        return dt, False
    return None


def parse_dt(s: str) -> datetime | None:
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None
