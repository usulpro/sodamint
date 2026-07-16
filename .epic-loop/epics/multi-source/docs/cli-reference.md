# CLI Reference

> **SUPERSEDED 2026-07-17 — kept for history only, not being built.** The
> strategic reset (see `../decision-log.md`) dropped the in-app CLI: agents keep
> the machine awake by wrapping themselves in `systemd-inhibit --why="…" -- <cmd>`,
> which already provides acquire/release/list. This file describes the retired
> lease-based CLI design.

All subcommands live on the existing `sodamint` entrypoint. With **no**
subcommand, `sodamint` launches the tray daemon (today's behavior). With a
recognized subcommand, it acts as a short-lived **client** that only
reads/writes lease files — it does **not** start the GUI and does **not**
require the daemon to be running.

## Synopsis

```
sodamint                                       launch the tray daemon (no subcommand)

sodamint acquire  --context <text> [options]   create a lease; prints <lease-id> to stdout
sodamint release  <lease-id>                   remove a lease (idempotent)
sodamint heartbeat <lease-id>                  refresh a lease's liveness timestamp
sodamint list     [--json]                     list active leases
sodamint status   [--json]                     show overall state (awake? / lease count)
sodamint run      --context <text> [options] -- <cmd> [args...]
                                               acquire, run <cmd>, release on exit
```

## `acquire`

Creates one lease and prints its id (the only thing on stdout, so it is safe to
capture with `id=$(sodamint acquire ...)`).

| Option | Default | Meaning |
| --- | --- | --- |
| `--context <text>` | *required* | Human-readable label shown in the tray, e.g. `"epic-loop impl of <slug> in ~/proj/foo"`. |
| `--id <id>` | generated UUID | Caller-chosen stable id. Re-acquiring the same id **updates** the lease instead of creating a duplicate (idempotent). |
| `--pid <pid>` | caller's parent PID | Process whose liveness backs this lease. Used by the watchdog's PID check. Pass `--pid 0` to opt out of PID-based liveness. |
| `--watch <file>` | none | File whose mtime signals "still working"; if it stops changing for `--stale`, the lease is considered stale. |
| `--stale <duration>` | `30m` (only when `--watch`/heartbeat used) | Max quiet time before a watch/heartbeat lease is auto-released. See duration format below. |
| `--json` | off | Print the created lease as a JSON object instead of a bare id. |

## `release <lease-id>`

Removes the lease file. Idempotent: releasing an unknown/already-gone id exits
`0` and does nothing. This is what an agent calls in its normal teardown.

## `heartbeat <lease-id>`

Refreshes the lease's `last_heartbeat` timestamp (used by heartbeat-based
liveness). No-op with exit `0` if the lease no longer exists — a manually
removed lease is **not** resurrected by a late heartbeat.

## `list [--json]`

Lists active leases: id, context, age, pid, liveness mode, and (if applicable)
time-until-stale. `--json` emits an array for scripting. This is the same data
the tray shows.

## `status [--json]`

One-line overall state: whether the machine is currently being kept awake and
how many leases hold it. `--json` emits `{ "awake": bool, "leases": N }`.

## `run --context <text> [options] -- <cmd> [args...]`

Scope-guard wrapper and the **recommended** shape for agents that can wrap their
work: it `acquire`s a lease, runs `<cmd>`, and `release`s the lease when `<cmd>`
exits **for any reason** (success, failure, signal). This makes a leaked lease
impossible. Accepts the same `--watch` / `--stale` / `--id` options as
`acquire`. Exit code is that of `<cmd>`.

## Duration format

`--stale` accepts `<int><unit>` where unit is `s`, `m`, or `h` (e.g. `90s`,
`30m`, `2h`), or a bare integer meaning seconds.

## Exit codes

`0` success (including idempotent no-ops); `2` invalid arguments; `1` runtime
error (e.g. lease directory not writable). `run` forwards `<cmd>`'s exit code.

## Examples

```bash
# Agent, explicit acquire/release around a long session:
id=$(sodamint acquire --context "epic-loop impl of multi-source in ~/proj/sodamint" \
                      --watch .epic-loop/epics/multi-source/.runtime/progress-log.jsonl \
                      --stale 30m)
# ... long agent work, optionally: sodamint heartbeat "$id" ...
sodamint release "$id"

# Agent that can wrap its command — no leak possible:
sodamint run --context "nightly build" -- ./build-all.sh

# What is keeping the machine awake right now?
sodamint list
```
