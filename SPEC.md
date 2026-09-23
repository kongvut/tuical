# SPEC — index

Tuical spec is split by domain. Start at `core/SPEC.md` for the project
overview, then read the feature files relevant to the work in hand.

## core/

| File | Covers |
|---|---|
| [`core/SPEC.md`](core/SPEC.md) | Overview, goal, non-goals, stack, module layout, milestones, roadmap, design decisions, open questions |
| [`core/data-model.md`](core/data-model.md) | `Event` dataclass, JSON envelope, invariants, storage path, env vars |
| [`core/keybindings.md`](core/keybindings.md) | Master keymap, Esc handler, dispatch order, NO_COLOR |

## features/

| File | Covers |
|---|---|
| [`features/views.md`](features/views.md) | All 5 views + status bar + visual design + rendering contract |
| [`features/events.md`](features/events.md) | Add/edit/delete flow, form fields, validator, save semantics |
| [`features/ics.md`](features/ics.md) | RFC 5545 VEVENT import/export — scope, round-trip guarantees, limits |
| [`features/ux.md`](features/ux.md) | Search, command palette, help overlay, confirm prompts, NO_COLOR fallback |

## Quick links by topic

- "How does an event get saved?" → `core/data-model.md` + `features/events.md`
- "What keys does `?` show?" → `core/keybindings.md` + `features/ux.md` (help section)
- "Add a new view" → `features/views.md` (rendering contract) + `core/keybindings.md` (dispatch)
- "Why no RRULE?" → `core/SPEC.md` (non-goals) + `features/ics.md` (v0.4 limitation)
- "Round-trip `.ics`" → `features/ics.md` (round-trip guarantees section)
- "Run on a server with no TERM" → `features/ux.md` (NO_COLOR section)
