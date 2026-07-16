# Watch Mode & Liveness

> **SUPERSEDED 2026-07-17 — kept for history only, not being built.** The
> strategic reset (see `../decision-log.md`) removed the watchdog entirely:
> logind releases a holder's inhibitor when the process dies (kernel closes the
> fd), and the "alive but hung" case is handled by the user manually dropping
> the source from the tray. The lease-file model and liveness signals below are
> retired. Current data-source/release mechanics live in
> [`data-source.md`](data-source.md).

## Why

A lease is a promise that "real work is still happening." Agents crash, hang,
or forget to release. Without a liveness check, one dead agent keeps the machine
awake all night. Watch mode makes the lease **self-expiring** so the machine
sleeps once work actually stops, not once a human notices.

## The lease file (shared state)

Each lease is one JSON file, written atomically (temp file + `rename`) so the
tray never reads a half-written file:

```
$XDG_RUNTIME_DIR/sodamint/leases/<id>.json
{
  "id": "8f3c…",
  "context": "epic-loop impl of multi-source in ~/proj/sodamint",
  "created_at": 1752489671,
  "pid": 48213,
  "pid_start": 92ha1b…,        // process start-time token, PID-reuse guard
  "watch_file": "…/progress-log.jsonl",   // optional
  "stale_after": 1800,                     // optional, seconds
  "last_heartbeat": 1752491000             // optional
}
```

`$XDG_RUNTIME_DIR` (tmpfs) is deliberate: it is wiped on logout/reboot, so no
lease can survive a session and wrongly keep tomorrow's machine awake.

## The three liveness signals

A watchdog timer in the tray daemon (`GLib.timeout_add_seconds`, default 60s)
evaluates every lease against whichever signals it carries. A lease is **dead**
if any active signal says so:

1. **PID liveness (always on unless `--pid 0`).** `os.kill(pid, 0)` — if it
   raises `ESRCH`, the process is gone → dead. Cheap, automatic, needs nothing
   from the agent.
2. **PID-reuse guard.** At `acquire`, the process start-time is recorded
   (`pid_start`, from `/proc/<pid>/stat`). If the PID is alive but its
   start-time no longer matches, the original process died and the OS reused the
   number → treated as **dead**. Prevents a false "still alive".
3. **Watch-file mtime (opt-in via `--watch`).** If `now - mtime(watch_file) >
   stale_after` → stale → dead. For work that naturally churns a file (a log, a
   checkpoint). If the file is missing, that also counts as stale.
4. **Heartbeat (opt-in).** `sodamint heartbeat <id>` refreshes `last_heartbeat`;
   if `now - last_heartbeat > stale_after` → dead. For work with no naturally
   churning file — the agent pings on its own cadence.

Signals combine with OR: whichever fires first wins. PID liveness is the free
baseline; `--watch`/heartbeat add the "alive but hung" case that PID checks miss.

## Who cleans a lease, and when — the matrix

This is the crux. "Cleaning" = deleting the lease file so it stops counting.

| Situation | Who deletes the lease | When |
| --- | --- | --- |
| Agent finishes normally | the agent (`release`, or `run --` on exit) | immediately |
| Agent crashes hard (process gone) | daemon watchdog, via PID check | ≤ 1 watchdog tick |
| Agent hangs (process alive, doing nothing) | daemon watchdog, via watch-file/heartbeat staleness | ≤ `stale_after` + 1 tick |
| PID reused by unrelated process | daemon watchdog, via start-time guard | ≤ 1 tick |
| User manually drops it in the tray | the tray (`Release this source`) | immediately |
| **Tray (daemon) not running when agent dies** | **nobody, until the daemon next starts** | on next daemon start (reconciliation pass) |
| Logout / reboot | the OS (tmpfs `$XDG_RUNTIME_DIR` wiped) | at session end |

The one gap is deliberate and bounded: **while the daemon is down, nothing runs
the watchdog.** That is fine because while the daemon is down there is also no
inhibitor — the machine is free to sleep anyway. Stale files just sit there
harmlessly and are pruned when the daemon restarts (it runs a full
reconciliation on startup before holding the lock) or vanish at the next reboot.

## Edge cases (validated)

**1. "I quit Sodamint myself while agents are working."**
The daemon exits → the single inhibitor is released → machine may sleep. Lease
files remain on disk. Agents keep running but are no longer protected. Mitigation
is in the UI: quitting with active leases **warns first**
(see [`tray-ux.md`](tray-ux.md)). We deliberately do **not** auto-delete leases
on quit, so a restart resumes protection and the watchdog then prunes the dead
ones. Net: quitting is an informed choice, never a silent loss with orphaned
files that mislead a later run.

**2. "The process died but its lease file is still there."**
Exactly what the watchdog exists for. PID check removes it within one tick; if
the agent also gave `--watch`/heartbeat, that is a second independent catch. If
the daemon happens to be down, the file is inert (no inhibitor) and is pruned on
the next start. So a leftover file never means "silently awake forever".

**3. Agent detaches / re-parents (PID no longer meaningful).**
The agent should pass a `--watch` file or send heartbeats; PID liveness alone is
unreliable for daemonized work. If it gives neither and `--pid 0`, the lease has
**no** auto-expiry and can only be cleared by `release`, manual tray removal, or
reboot — `list`/tray flag such leases as "no liveness" so they are visible.

**4. Two agents, same watch file, one dies.**
Leases are independent files with independent PIDs. The dead one is pruned by its
PID check; the live one keeps the (still-fresh) watch file and survives. No
cross-talk.

**5. Half-written lease / unparseable file.**
Atomic write avoids partial reads; additionally the daemon skips any file that
fails to parse (readJsonSafe pattern) rather than crashing, and the watchdog
may delete a persistently-unparseable file after a grace period.

**6. Clock skew / mtime in the future.**
Ages and staleness clamp at zero; a future timestamp is treated as "just now",
never as "infinitely stale", to avoid spurious releases around clock changes.

**7. Manual tray release while the agent still runs.**
The lease file is removed; the agent's later `heartbeat`/`release` are no-ops
(a removed lease is not resurrected). Manual removal is authoritative — the user
decided this source no longer justifies keeping the machine awake.

**8. Re-acquire with the same `--id`.**
Updates the existing lease in place (new context/timestamps), never creates a
duplicate — so an agent that restarts a phase does not stack leases.

## Defaults

- Watchdog interval: 60s.
- `stale_after`: 30m when `--watch`/heartbeat is used and no explicit value is
  given (matches the stated overnight tolerance).
- PID liveness: on by default; `--pid 0` opts out.
- Startup reconciliation: on every daemon start, evaluate all existing leases
  once **before** acquiring the inhibitor, so a restart never re-holds the lock
  for already-dead sources.
