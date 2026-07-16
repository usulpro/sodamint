# Epic Problem Framing

> **Reshaped 2026-07-17 (strategic reset).** The original framing proposed a
> lease/refcount/watchdog keep-awake *service*. A design review found that
> `systemd-inhibit`/logind already provides multi-source keep-awake, reference
> counting, "who holds it", and crash cleanup — so building that would rebuild
> the OS. The epic now targets only the two gaps logind leaves: **visibility**
> and **manual drop**. See the reset note in `decision-log.md`.

## Problem

Sodamint today is a single on/off toggle: one tray click holds one
`systemd-inhibit` lock, and `self.proc` is the whole state. The real workload is
**AI coding agents running long autonomous sessions** (via `epic-loop`), often
overnight, frequently **several in parallel** across projects. Each already
needs the machine awake for exactly as long as *it* works.

The correct primitive for that already exists: each agent can be launched under
`systemd-inhibit --why="…" -- <agent>`, and logind then keeps the machine awake
while **any** holder lives and lets it sleep when the last one exits — including
automatic release when a holder crashes (the kernel closes its fd). What logind
does **not** give is a human-facing view or control:

- There is no at-a-glance answer to **"why is my machine awake right now, and
  who is holding it?"** — `systemd-inhibit --list` exists but is a terminal
  command, not something visible from the tray while you work.
- There is no one-click way to **drop a specific source** — e.g. an agent that
  is technically alive but hung, or a lock someone forgot — without dropping to
  a terminal to find and kill the right PID.

Sodamint's single boolean toggle addresses neither: it shows only its own state
and controls only its own lock.

## Desired Outcome

Sodamint becomes a **tray dashboard and control surface over logind's inhibitor
list** — a thin UI layer, not a new service:

- The tray shows **every active idle/sleep inhibitor** — who is holding the
  machine awake, why, and by which PID — read live from logind.
- The icon reflects reality: **active whenever anyone holds an idle/sleep
  inhibitor**, inactive when nobody does. It answers "is something keeping this
  machine awake, and how many things?" without a terminal.
- **Agent sources are highlighted.** Inhibitors an agent set following the
  contract (`--who=sodamint-agent`, see [`agent-integration.md`](agent-integration.md))
  are visually distinguished from arbitrary system inhibitors, so the user can
  tell "my overnight agents" apart at a glance.
- External sources are **read-only** — Sodamint shows them but never drops
  another process's lock (see Non-Scope). The existing **manual keep-awake
  toggle keeps working unchanged** and is the one lock the user controls from
  the tray; it now also appears as a row in the dashboard.

All keep-awake *mechanics* — reference counting, "awake while any holder lives",
crash cleanup — remain logind's job. Sodamint never re-implements them.

## Scope

- **Read inhibitors from logind** via `org.freedesktop.login1.Manager.
  ListInhibitors()` over D-Bus (structured, no parsing, no new dependency),
  filtered to idle/sleep holders. See [`data-source.md`](data-source.md).
- **Dynamic tray menu** listing each active idle/sleep inhibitor with who / why
  / pid (and age if cheaply derivable from `/proc`), read-only, with agent
  sources highlighted. Both tray backends. See [`tray-ux.md`](tray-ux.md).
- **Icon/status driven by the inhibitor count**, not just our own toggle.
- **Keep the manual toggle**, mechanism unchanged; it is the only tray control
  and the only lock Sodamint releases (its own). See [`data-source.md`](data-source.md).
- **Agent-integration contract** — a documented `systemd-inhibit` wrapper and
  `--who`/`--why` message format agents follow so their locks appear and are
  highlighted. See [`agent-integration.md`](agent-integration.md).
- **Docs**: update `CLAUDE.md` to the narrowed source-of-truth model and point
  agents at the integration contract.

## Non-Scope

- **No lease store, no in-app reference counting, no CLI, no watchdog.** logind
  already provides all of it; rebuilding it was the rejected old design.
- **No "alive but hung" auto-detection** (watch-files / heartbeats). The user
  chose manual drop (they see a stuck source and drop it) over building
  liveness heuristics. Documented, not solved.
- **No acquiring locks on behalf of agents.** Agents wrap themselves in
  `systemd-inhibit`; Sodamint only observes.
- **No dropping/killing external sources.** External inhibitors are read-only
  (D14); Sodamint releases only its own manual lock.
- **No macOS port** (D9) — the whole rationale collapses there.
- **No preventing screen blanking / lock.** As today, Sodamint targets system
  sleep/idle via logind; the DPMS / DE-screensaver layer is left alone.
- **No network / remote control.** Everything is local to one machine/session.

## Constraints

- Stay a single-file GTK3 app plus its icons/installer; **no new runtime
  dependency** beyond the current `python3-gi` / AppIndicator / systemd set
  (`Gio` D-Bus is already available through `python3-gi`).
- Keep both tray backends (AppIndicator + `Gtk.StatusIcon`) working.
- Degrade gracefully where logind is not reachable (D-Bus unavailable → fall
  back to `systemd-inhibit --list`; no inhibitors / errors → empty list, not a
  crash).
- `_refresh()` stays the single UI-repaint point.

## Open Questions

Tracked in `decision-log.md` (age column source, agent-highlight style, quit
confirm).
