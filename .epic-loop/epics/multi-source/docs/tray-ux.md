# Tray UX Decision

> **Reshaped 2026-07-17.** Rows come from logind's live inhibitor list, not from
> a lease store. External sources are **read-only** (Sodamint never drops another
> process's lock — D14); the only control is our own manual toggle. Agent-set
> inhibitors (`who=sodamint-agent`) are visually highlighted. See
> `decision-log.md` (D10–D18), [`data-source.md`](data-source.md), and
> [`agent-integration.md`](agent-integration.md).

## Goal

Turn the tray from a boolean toggle into a live view of **who is holding the
machine awake**, while keeping the one-click manual use that exists today. The
data behind every row is logind's inhibitor registry — Sodamint is the window
onto it, not the accountant.

## Icon state

The icon is **active** whenever ≥1 idle/sleep inhibitor exists (from *any*
process, D13), and **inactive** when none do. Sodamint's own manual toggle is no
longer special — it is one inhibitor among the others. This makes the tray icon
a truthful "is anything keeping this machine awake?" light.

## Menu layout

```
┌────────────────────────────────────────────┐
│ Awake — 3 sources                     (hdr) │   status header, insensitive
├────────────────────────────────────────────┤
│ ◆ epic-loop · sodamint · Phase 2 · pid 48213│   agent source (highlighted)
│ ● nightly build · pid 51002                 │   plain external source
│ ★ Sodamint keep-awake (this) · pid 5591     │   our own manual lock
├────────────────────────────────────────────┤
│ ☑ Keep awake (manual)                       │   manual toggle (checkbox)
├────────────────────────────────────────────┤
│ Quit                                        │
└────────────────────────────────────────────┘
```

- **Status header** — `Awake — N sources` or `Idle` when empty. Insensitive
  (label only), same role as today's `Status: on/off`.
- **One row per inhibitor** — a marker glyph, the `why` string (falling back to
  `who` when empty), and the pid. An age (`2h14m`) is appended when it can be
  derived from `/proc/<pid>` start-time (open question in `decision-log.md`).
  Rows are **read-only labels** — clicking a source does nothing; there is no
  per-source release (D14). The row exists to answer "who is holding the machine
  awake." Row types are distinguished by glyph:
  - `◆` **agent source** — `who == sodamint-agent` (see
    [`agent-integration.md`](agent-integration.md)); the row Sodamint highlights.
  - `★` **our own manual lock** — pid matches `self.proc`.
  - `●` **any other inhibitor** — arbitrary system/app source.
- **Keep awake (manual)** — the classic checkbox, the **only control** in the
  menu. Checking it starts our own `systemd-inhibit … sleep infinity` subprocess
  (today's `start()`); unchecking terminates it (`stop()`). This is unchanged
  from today and is how the user releases the one lock Sodamint owns. The
  feedback-loop guard (`handler_block_by_func`) is kept.
- **Quit** — see below.

## No release of external sources (D14)

logind has **no API to release another process's inhibitor** — the lock is an fd
owned by the holder — and killing the holder was rejected as too blunt. So the
tray offers **no drop action for external sources**; they are display-only. The
only lock the tray releases is our own manual one, via the checkbox above (or by
quitting). To stop an external source the user acts on that process directly,
outside Sodamint.

## Both tray backends

The dynamic list must render on both paths described in `CLAUDE.md`: the
AppIndicator path (`self.indicator`) and the `Gtk.StatusIcon` fallback
(`self.status_icon` + `self._menu`). Because AppIndicator menus are static once
set, `_refresh()` **rebuilds** the inhibitor section (or resets the whole menu)
rather than mutating labels in place, and re-applies it via `set_menu()`.
`_refresh()` stays the single place that repaints all UI from the current
inhibitor list.

## Refresh triggers

logind emits no "inhibitor added/removed" signal, so `_refresh()` runs on:
(a) a `GLib.timeout` poll of `ListInhibitors()` every few seconds, and (b) when
the menu is popped up (so a user opening the tray sees fresh data immediately).
Age labels advance at the poll cadence — no separate per-second timer.

## Quit behavior

Quitting Sodamint stops **only our own** `systemd-inhibit` subprocess. Every
external inhibitor is a separate process that keeps running and keeps holding
its own lock — so **quitting does not put the machine to sleep** if agents are
still working. This is strictly safer than the old lease design, where quit
dropped the single shared lock.

- If our manual toggle is **off**, quit immediately (nothing of ours to drop).
- If our manual toggle is **on**, a light confirm is optional (we are about to
  drop the one lock we own): `"The manual keep-awake will be released on quit.
  Other sources are unaffected. Quit?"` — leaning toward showing it only in that
  case.

## Non-goals for the UI

- No control over external sources at all — no release, no kill, no edit. They
  are read-only labels (D14).
- No per-source styling beyond the three row-type glyphs (`◆`/`★`/`●`).
- No history of ended sources in the menu (that is log territory, not tray).
- No re-creating logind's bookkeeping — the tray reflects logind, it does not
  cache or reconcile state of its own.
