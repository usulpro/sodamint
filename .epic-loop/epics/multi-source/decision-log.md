# Decision Log

## Strategic Reset — 2026-07-17

A prior design session (Claude Code transcript `e7c91d0e`, project folder
`sodamint/Sodamint`) evaluated whether the lease/refcount/watchdog feature is
worth building on Linux and concluded it is **~80% redundant with
`systemd-inhibit`/logind**, including the hardest part — crash cleanup, which
the kernel does natively by closing the holder's fd. That analysis was not in
scope when Phase 1 shaping first landed, so the epic was reshaped.

User decision (2026-07-17): **do not rebuild what logind already does.** Keep
only the genuinely missing pieces and make Sodamint a thin **tray UI layer over
`systemd-inhibit`**: show every active idle/sleep inhibitor (who / why / pid)
and let the user manually drop a source. No lease store, no in-app reference
counting, no watchdog, no CLI.

Decisions **D1–D8** below are **superseded** by this reset and kept only for
history. **D9** (do not port to macOS) survives unchanged and is now even more
central. New decisions **D10–D17** define the reshaped architecture.

## Active Decisions

- **D9 — Do NOT port to macOS.** `caffeinate`/`pmset` provide the engine,
  process-watch, reference counting, and "who holds it" natively, and the
  AI-agent niche is already served (Adrafinil, Macchiato, Amphetamine,
  Insomnia). The Linux gap that justifies Sodamint does not exist on macOS.
  See [`docs/macos-feasibility.md`](docs/macos-feasibility.md).
- **D10 — Sodamint is a UI over logind's inhibitor list, not a keep-awake
  service.** logind already does multi-source, reference counting, "who holds
  it", and crash cleanup (fd closed on holder death). Sodamint adds only the two
  things logind lacks: a **visual tray dashboard** of active inhibitors and a
  one-click **manual drop** of a source. All "stays awake" logic is delegated to
  logind. Supersedes D1–D8.
- **D11 — Read inhibitors via the login1 D-Bus API, not by scraping CLI text.**
  `org.freedesktop.login1.Manager.ListInhibitors()` returns structured tuples
  `(what, who, why, mode, uid, pid)` with no parsing and no new dependency
  (`Gio` ships with `python3-gi`). Scraping `systemd-inhibit --list` stdout is
  the documented fallback only if the D-Bus call is unavailable. See
  [`docs/data-source.md`](docs/data-source.md).
- **D12 — Show only inhibitors that actually keep the machine awake.** Filter
  `ListInhibitors()` to entries whose `what` contains `idle` or `sleep`
  (typically `mode=block`). Ignore `handle-power-key`, `shutdown`, `handle-lid`,
  etc. — they are not why the machine is awake.
- **D13 — The icon is active iff ≥1 idle/sleep inhibitor exists (from anyone).**
  Not just when Sodamint's own toggle is on. This is the core "why is my machine
  awake?" answer. Sodamint's own manual lock is simply one entry among the
  others.
- **D14 — Manual drop of an external source = signal its holder PID.** logind
  exposes no call to release another process's inhibitor — the lock is an fd
  owned by that process. "Release this source" therefore sends `SIGTERM` to the
  holding PID (with a confirm dialog, since it kills a real process). Dropping
  *our own* manual lock stays clean: terminate our `systemd-inhibit` subprocess
  as today. Killing another user's or a privileged PID may fail with `EPERM`;
  handle it gracefully and surface the error.
- **D15 — The manual toggle stays, unchanged in mechanism.** It still holds one
  `systemd-inhibit --what=idle:sleep … sleep infinity` subprocess (`self.proc`).
  It now also appears as a row in the dashboard, identified by our own PID. Its
  release path (terminate the subprocess) is the clean case of D14.
- **D16 — Refresh by polling `ListInhibitors()` on a modest timer plus on menu
  open.** login1 emits no "inhibitor added/removed" signal, so `_refresh()` runs
  on a `GLib.timeout` (a few seconds) and when the menu is popped up. AppIndicator
  menus are static once set, so `_refresh()` rebuilds the inhibitor section and
  re-applies it via `set_menu()`; the StatusIcon fallback rebuilds `self._menu`.
- **D17 — `self.proc` is the source of truth only for *our* manual lock; the
  live inhibitor list is the source of truth for the dashboard.** This narrows,
  rather than replaces, the current `CLAUDE.md` invariant: `is_on()` still means
  "our subprocess is alive", but the tray now also reflects inhibitors Sodamint
  does not own. `_refresh()` remains the single UI-repaint point. `CLAUDE.md`
  must be updated to say so.

## Open Questions

- **Age/"since when" per source.** login1 exposes no inhibitor start time. If we
  want an age column we must read `/proc/<pid>` start-time and compute it (no new
  dep). Leaning: show age when `/proc` is readable, omit otherwise — nice-to-have,
  not core.
- **SIGTERM vs escalate to SIGKILL on manual drop.** If a held process ignores
  SIGTERM, do we offer a follow-up SIGKILL? Leaning: SIGTERM only for v1; the
  list will simply still show it, and the user can retry.
- **Confirm dialog scope.** Confirm on every external drop (it kills a process)
  but drop our own manual lock without a prompt? Leaning: yes — our lock is not a
  process the user cares about losing.

## Superseded Decisions (old lease architecture, pre-2026-07-17 reset)

Kept for history only. All of the below are replaced by D10–D17; the machinery
they describe (lease files, in-app refcount, CLI, watchdog) is **not being
built** because logind already provides it.

- **D1 — Filesystem is the shared state; no bespoke IPC.** ~~JSON lease files
  under `$XDG_RUNTIME_DIR/sodamint/leases/`.~~ Superseded: logind's inhibitor
  registry is the shared state; no files of our own.
- **D2 — One inhibitor for the whole app, gated on `lease_count > 0`.**
  Superseded: each source holds its own inhibitor; logind reference-counts them.
- **D3 — `self.proc` stops being the source of truth; the lease set is.**
  Superseded by D17.
- **D4 — Storage in `$XDG_RUNTIME_DIR` (tmpfs).** Superseded: no lease storage.
- **D5 — Three OR-combined liveness signals (PID, watch-file, heartbeat).**
  Superseded: no watchdog; logind releases the fd on holder death, and the
  "alive but hung" case is handled by the user seeing it and dropping it (D14),
  which the user chose over building detection.
- **D6 — Quit warns but does not auto-delete leases.** Superseded: quitting drops
  only our own manual lock; external inhibitors are separate processes and are
  unaffected. See reshaped quit behavior in [`docs/tray-ux.md`](docs/tray-ux.md).
- **D7 — Manual removal is authoritative; late heartbeat does not resurrect.**
  Superseded: no leases, no heartbeat.
- **D8 — The manual tray toggle is just another lease.** Reframed by D15: the
  toggle is our own inhibitor, shown as one row among logind's list.
