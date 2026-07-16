# Data Source & Release Mechanics

How Sodamint reads the inhibitor list and how it drops a source. This replaces
the old `watch-mode.md` liveness model (superseded — see that file's banner).

## Reading inhibitors — login1 D-Bus (D11)

Primary source: logind's `ListInhibitors` method on
`org.freedesktop.login1.Manager`.

- Bus: system bus, service `org.freedesktop.login1`, object `/org/freedesktop/login1`.
- Method: `ListInhibitors() → a(ssssuu)`, one tuple per inhibitor:
  `(what, who, why, mode, uid, pid)`.
  - `what`  — colon list, e.g. `idle:sleep`, `handle-power-key`, `shutdown`.
  - `who`   — short holder name (the `--who`/comm of the acquirer).
  - `why`   — human reason string (the `--why`).
  - `mode`  — `block` or `delay`.
  - `uid`, `pid` — owner uid and holder pid.

Access from Python with `Gio` (already provided by `python3-gi`, **no new
dependency**):

```python
from gi.repository import Gio, GLib
bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
res = bus.call_sync(
    "org.freedesktop.login1", "/org/freedesktop/login1",
    "org.freedesktop.login1.Manager", "ListInhibitors",
    None, GLib.VariantType("(a(ssssuu))"),
    Gio.DBusCallFlags.NONE, -1, None,
)
inhibitors = res.unpack()[0]   # list of (what, who, why, mode, uid, pid)
```

### Filtering (D12)

Keep only inhibitors that actually keep the machine awake: `what` contains
`idle` or `sleep`. Drop `handle-power-key`, `handle-lid-switch`, `shutdown`,
etc. `mode=block` is the norm for keep-awake; `delay` holders may be shown but
are not why the machine stays up.

### Fallback

If the D-Bus call is unavailable (older logind, restricted bus), fall back to
scraping `systemd-inhibit --list --no-legend` / `--no-pager` and parsing the
`WHO/UID/USER/PID/COMM/WHAT/WHY/MODE` columns. Same filter applies. This is a
fallback only — D-Bus is the primary path because it is structured and
parse-free.

### Refresh cadence

logind emits no add/removed signal for inhibitors, so poll `ListInhibitors()` on
a `GLib.timeout` (a few seconds) and on menu popup. Cheap: a single D-Bus call
returning a small array.

### Age (open question)

logind does not expose an inhibitor's start time. If an age column is wanted,
derive it from the holder process: read `/proc/<pid>/stat` field 22 (starttime,
in clock ticks since boot), combine with `/proc/uptime` and `SC_CLK_TCK`. Show
the age when readable, omit otherwise. No new dependency. Marked as a
nice-to-have in `decision-log.md`.

## Dropping a source (D14)

There is **no logind method to release an inhibitor you do not own** — the lock
is an fd held by the acquiring process. Releasing therefore targets the holder
process itself.

| Source | How Sodamint drops it | Confirm? |
| --- | --- | --- |
| Our own manual lock (pid == `self.proc.pid`) | `self.proc.terminate()` then `.wait()` (today's `stop()`) | no |
| Any external inhibitor | `os.kill(pid, signal.SIGTERM)` | yes — it kills a real process |

Failure handling:

- `PermissionError` / `EPERM` — the pid belongs to another user or is
  privileged. Surface a dialog ("Not permitted to signal pid N"), do not crash.
- `ProcessLookupError` / `ESRCH` — the process already exited; just refresh, the
  row will be gone.
- After any drop attempt, re-poll `ListInhibitors()` and repaint so the list
  reflects reality within one refresh.

SIGTERM only for v1 (open question: offer SIGKILL escalation if a process
ignores SIGTERM). A process that ignores SIGTERM simply stays in the list and
the user can retry.

## Why this needs no watchdog, lease store, or CLI

- **"Awake while any holder lives"** — logind reference-counts inhibitors
  natively.
- **Crash cleanup** — when a holder dies, the kernel closes its fd and logind
  drops the inhibitor automatically; no PID watchdog needed.
- **"Who holds it" + context** — carried in the `who`/`why`/`pid` tuple already.
- **Acquire/release CLI** — `systemd-inhibit --why="…" -- <cmd>` already is it.

Sodamint adds only the window (list + icon) and the manual override (drop),
which are the two things logind does not surface itself.
