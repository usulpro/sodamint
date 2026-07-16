# Epic Problem Framing

## Problem

Sodamint today is a single on/off toggle: one tray click holds one
`systemd-inhibit` lock, and `self.proc` is the whole state. That does not fit
how the machine is actually used for long work. The primary workload is
**AI coding agents running long autonomous sessions** (via the `epic-loop`
framework), often left running overnight, frequently **several agents in
parallel** across different projects. Each of them independently needs the
machine to stay awake for as long as *it* is working, and no longer.

With a single manual toggle:

- Agents cannot programmatically request keep-awake — a human has to remember
  to flip it before leaving.
- There is no way to keep the machine awake "while any agent is still working"
  — the toggle is global and unaware of who needs it.
- When work finishes, the toggle stays on until a human turns it off, so the
  machine can stay awake pointlessly for hours.
- If an agent hangs or crashes, nothing notices; the machine stays awake with
  no live work behind it.
- There is zero visibility into *why* the machine is being kept awake or *who*
  requested it.

## Desired Outcome

Sodamint becomes a small **reference-counted keep-awake service** with a CLI,
so that:

- Any process (an agent, a script, the user) can **acquire** a keep-awake
  *lease* with a human-readable context label and **release** it when done.
- The machine stays awake while **at least one** live lease exists, and is
  allowed to sleep the moment the last one is released. One `systemd-inhibit`
  lock for the whole app, gated on `lease_count > 0`.
- The **tray shows every active lease** — who is holding the machine awake and
  since when — not just a boolean.
- A **watchdog** auto-releases dead or stale leases (crashed agent, hung
  process, forgotten release), so a machine left overnight sleeps once real
  work stops, instead of staying awake until morning.
- The existing manual toggle keeps working, expressed as just one more lease.

## Scope

- File-based lease store (the filesystem is the shared state; CLI and tray
  agree through it, with no bespoke IPC protocol). See
  [`tray-ux.md`](tray-ux.md) and [`watch-mode.md`](watch-mode.md).
- CLI subcommands on the existing `sodamint` entrypoint: `acquire`, `release`,
  `heartbeat`, `list`, `status`, and a `run -- <cmd>` scope-guard wrapper. Full
  syntax in [`cli-reference.md`](cli-reference.md).
- Reference-counted single inhibitor in the tray daemon.
- Dynamic tray menu listing active leases with context + age + manual release.
- Watchdog with three independent liveness signals: PID liveness (with
  start-time guard), watch-file mtime, and heartbeat. Edge-case behavior in
  [`watch-mode.md`](watch-mode.md).
- A written assessment of whether to port the whole feature to macOS, backed by
  research into existing tools and demand. See
  [`macos-feasibility.md`](macos-feasibility.md).

## Non-Scope

- Actually building the macOS port. This epic only decides whether it is worth
  doing; current expectation (see the feasibility doc) is "no".
- Network / remote control of leases (everything is local to one machine/user).
- Preventing **screen blanking / lock** — Sodamint keeps the *system* awake via
  logind; the display-blank layer (DPMS / DE screensaver) is deliberately left
  alone, as today. Documented, not solved.
- Per-lease *different* inhibitor scopes (e.g. one lease blocks only idle,
  another blocks suspend). All leases map to the same `idle:sleep` block.

## Constraints

- Stay a single-file GTK3 app plus its icons/installer, no new runtime
  dependencies beyond the current `python3-gi` / AppIndicator / systemd set.
- The CLI must work whether or not the tray daemon is currently running
  (it only touches lease files); the daemon reconciles when it (re)starts.
- Keep the two tray backends (AppIndicator + `Gtk.StatusIcon`) working.
- Lease writes must be atomic (temp + rename) so the tray never reads a
  half-written file.

## Open Questions

- Should quitting the tray while leases are still active **warn** the user,
  **auto-release** everything, or leave leases on disk for the next start?
  (Leaning: warn, leave on disk — see decision log.)
- Default `--stale` window when a watch-file/heartbeat is given but no explicit
  timeout? (Leaning: 30 min, matching the user's stated overnight tolerance.)
- Should `heartbeat` on a manually-removed lease stay a silent no-op (manual
  removal wins) or re-create it? (Leaning: no-op.)
