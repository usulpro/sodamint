# Tray UX Decision

## Goal

Turn the tray from a boolean toggle into a live view of **who is holding the
machine awake and since when**, while keeping the one-click manual use that
exists today.

## Icon state

Unchanged mechanism, new trigger: the icon is **active** whenever
`lease_count > 0` and **inactive** when there are no leases. The manual toggle
is no longer special — it is simply one lease among the others.

## Menu layout

```
┌────────────────────────────────────────────┐
│ Awake — 3 sources                     (hdr) │   status header, insensitive
├────────────────────────────────────────────┤
│ ● epic-loop multi-source · 2h14m       ▸    │   one row per lease → submenu
│ ● nightly build · 41m                  ▸    │
│ ● manual (tray) · 6m                   ▸    │
├────────────────────────────────────────────┤
│ ☐ Keep awake (manual)                       │   manual lease toggle (checkbox)
├────────────────────────────────────────────┤
│ Quit                                        │
└────────────────────────────────────────────┘
```

- **Status header** — `Awake — N sources` or `Idle` when empty. Insensitive
  (label only), same role as today's `Status: on/off`.
- **One row per lease** — a bullet, the context label, and a compact age
  (`2h14m`). Each row opens a small submenu:
  ```
  ● epic-loop multi-source · 2h14m ▸
        pid 48213 · watch: progress-log.jsonl · stale in 24m
        ─────────────
        Release this source
  ```
  The submenu shows the liveness backing (pid / watch-file / heartbeat) and,
  for watch/heartbeat leases, the countdown to stale. `Release this source`
  lets the user manually drop a lease (e.g. a hung agent) without a terminal.
- **Keep awake (manual)** — the classic checkbox. Checking it creates a lease
  with context `manual (tray)`; unchecking releases it. This preserves the
  current muscle-memory: one click keeps the machine awake indefinitely until
  clicked off. The feedback-loop guard (`handler_block_by_func`) is kept.
- **Quit** — see below.

## Both tray backends

The dynamic list must render on both paths described in `CLAUDE.md`: the
AppIndicator path (`self.indicator`) and the `Gtk.StatusIcon` fallback
(`self.status_icon` + `self._menu`). Because AppIndicator menus are static once
set, `_refresh()` **rebuilds** the lease section (or resets the whole menu)
rather than mutating labels in place, and re-applies it via `set_menu()`.
`_refresh()` stays the single place that repaints all UI from the lease set —
the architecture rule in `CLAUDE.md` is preserved, only its "source of truth"
moves from `self.proc` to "the set of live leases".

## Refresh triggers

`_refresh()` runs on: (a) `Gio.FileMonitor` events on the leases directory
(a lease created/removed/updated by any CLI call), and (b) each watchdog tick
(so ages and stale-countdowns advance and auto-released leases disappear). Age
labels update at most once per watchdog interval — no separate per-second timer.

## Quit behavior (decision)

Quitting the tray stops the process, which drops the single `systemd-inhibit`
lock — so **the machine can sleep again even if lease files still exist**. To
avoid silently removing protection from running agents:

- If **no** leases are active, quit immediately (today's behavior).
- If leases **are** active, show a confirm dialog:
  `"3 sources are keeping this machine awake. Quit anyway? The machine may sleep."`
  Quit only on confirm.
- On quit, lease files are **left on disk**. They are not the daemon's to
  delete, and leaving them means a later `sodamint` restart re-reads them,
  resumes enforcement, and lets the watchdog prune whichever have since died.

This "warn, don't auto-delete" choice is analyzed further, with the full
crash/quit/stale matrix, in [`watch-mode.md`](watch-mode.md).

## Non-goals for the UI

- No per-lease icons or colors beyond active/inactive.
- No editing of a lease from the tray (only release).
- No history of released leases in the menu (that is log territory, not tray).
