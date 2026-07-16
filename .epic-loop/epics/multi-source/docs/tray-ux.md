# Tray UX Decision

> **Reshaped 2026-07-17.** Rows come from logind's live inhibitor list, not from
> a lease store; "Release" signals the holder PID, not a file delete; quit only
> drops our own lock. See `decision-log.md` (D10–D17) and
> [`data-source.md`](data-source.md).

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
│ ● epic-loop multi-source · pid 48213   ▸    │   one row per inhibitor → submenu
│ ● nightly build · pid 51002            ▸    │
│ ● Sodamint keep-awake (this) · pid 5591 ▸   │   our own manual lock, flagged
├────────────────────────────────────────────┤
│ ☐ Keep awake (manual)                       │   manual toggle (checkbox)
├────────────────────────────────────────────┤
│ Quit                                        │
└────────────────────────────────────────────┘
```

- **Status header** — `Awake — N sources` or `Idle` when empty. Insensitive
  (label only), same role as today's `Status: on/off`.
- **One row per inhibitor** — a bullet, the `why` string (falling back to `who`
  when empty), and the pid. An age (`2h14m`) is appended when it can be derived
  from `/proc/<pid>` start-time (open question in `decision-log.md`). Each row
  opens a small submenu:
  ```
  ● epic-loop multi-source · pid 48213 ▸
        who: epic-loop · what: idle:sleep · mode: block · uid 1000
        ─────────────
        Release this source
  ```
  The submenu shows the raw logind fields (who / what / mode / uid).
  `Release this source` drops that inhibitor (see below).
- **Keep awake (manual)** — the classic checkbox. Checking it starts our own
  `systemd-inhibit … sleep infinity` subprocess (today's `start()`); unchecking
  terminates it (`stop()`). Preserves the current muscle-memory. The
  feedback-loop guard (`handler_block_by_func`) is kept.
- **Quit** — see below.

## Release semantics (the key change)

logind has **no API to release another process's inhibitor** — the lock is an fd
owned by the holder. So "Release this source" depends on whose lock it is:

- **Our own manual lock** (pid matches `self.proc`): terminate the subprocess
  cleanly, exactly like unchecking the toggle. No confirm needed.
- **Any external inhibitor**: send `SIGTERM` to its pid (D14). This kills a real
  process (e.g. an agent), so it **confirms first**:
  `"Release "epic-loop multi-source" (pid 48213)? This sends SIGTERM to that
  process."` If the kill fails (`EPERM` for another user's or a privileged pid,
  `ESRCH` if already gone), surface it in a dialog and refresh; never crash.

The submenu row is the only place a source is dropped from the tray.

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

- No per-source icons or colors beyond active/inactive.
- No editing of an inhibitor from the tray (only release).
- No history of released sources in the menu (that is log territory, not tray).
- No re-creating logind's bookkeeping — the tray reflects logind, it does not
  cache or reconcile state of its own.
