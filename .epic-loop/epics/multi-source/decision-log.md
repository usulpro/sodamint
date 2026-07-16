# Decision Log

## Active Decisions

- **D1 — Filesystem is the shared state; no bespoke IPC.** Each lease is one
  JSON file under `$XDG_RUNTIME_DIR/sodamint/leases/`. CLI writes/removes files;
  the tray daemon watches the directory. Chosen over a socket or DBus service
  because it needs no protocol, gives natural per-lease reference counting, and
  decouples CLI lifetime from the daemon (CLI works even when the daemon is
  down). Tradeoff: no instant "acquire failed" feedback — acceptable here.
- **D2 — One inhibitor for the whole app, gated on `lease_count > 0`.** Not one
  `systemd-inhibit` per lease. A single lock is sufficient to keep the machine
  awake; reference counting is done in the daemon over the lease set.
- **D3 — `self.proc` stops being the source of truth; the lease set is.** The
  inhibitor and all UI derive from the live leases. This revises the `CLAUDE.md`
  invariant and must be reflected there. `_refresh()` remains the single
  UI-repaint point.
- **D4 — Storage in `$XDG_RUNTIME_DIR` (tmpfs), not `~/.local/state`.** Leases
  are ephemeral by nature; tmpfs is wiped on logout/reboot so no lease can
  wrongly survive a session. Rejected persistent storage for that reason.
- **D5 — Three OR-combined liveness signals: PID (+start-time guard), watch-file
  mtime, heartbeat.** PID liveness is the free automatic baseline; watch/
  heartbeat add the "alive but hung" case. Start-time token guards against PID
  reuse. See [`docs/watch-mode.md`](docs/watch-mode.md).
- **D6 — Quit warns but does not auto-delete leases.** With active leases, Quit
  confirms first; lease files are left on disk so a restart resumes enforcement
  and the watchdog prunes the dead ones. Rejected auto-deleting on quit (would
  silently drop protection and lose restart-resume).
- **D7 — Manual removal is authoritative; late heartbeat does not resurrect.**
  `heartbeat`/`release` on a missing lease are no-ops. Re-acquiring the same
  `--id` updates in place rather than duplicating.
- **D8 — The manual tray toggle is just another lease** (context `manual
  (tray)`), so there is one uniform model, not a special-cased boolean.
- **D9 — Do NOT port to macOS.** `caffeinate`/`pmset` provide the engine,
  process-watch, reference counting, and "who holds it" natively, and the
  AI-agent niche is already served (Adrafinil, Macchiato, Amphetamine,
  Insomnia). The Linux gap that justifies Sodamint does not exist on macOS.
  See [`docs/macos-feasibility.md`](docs/macos-feasibility.md).

## Historical Decisions

- None recorded yet.
