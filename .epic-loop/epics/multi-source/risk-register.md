# Risk Register

> **Reshaped 2026-07-17.** Old lease/watchdog risks are retired at the bottom;
> the active table reflects the logind-dashboard architecture.

## Active Risks

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| `login1 ListInhibitors` unavailable (old logind / restricted bus) | Medium: dashboard shows nothing | D-Bus is primary; documented fallback to parsing `systemd-inhibit --list`; treat errors as empty list, never crash | open |
| Manual drop kills the wrong / an unintended process | High: a real agent is terminated | Confirm dialog shows why + pid before SIGTERM; our own lock is released without a kill; only idle/sleep holders are listed | open |
| Killing another user's or a privileged pid fails (`EPERM`) | Low: drop is a no-op | Catch `PermissionError`, surface a dialog, refresh; do not crash | open |
| Process already gone between poll and drop (`ESRCH`) | Low: stale row | Catch `ProcessLookupError`, just re-poll; row disappears | open |
| Poll interval too slow → stale list; too fast → churn | Low: minor UX lag or wasted cycles | Modest `GLib.timeout` (a few seconds) + refresh on menu popup; single small D-Bus call is cheap | open |
| AppIndicator menu is static; dynamic list won't update | Medium: tray shows stale rows | `_refresh()` rebuilds the section and re-applies via `set_menu()`; verify on both AppIndicator and StatusIcon | open |
| Age from `/proc/<pid>` unavailable or racy | Low: no/incorrect age | Age is nice-to-have; omit when `/proc` unreadable; clamp negatives to zero | open |
| Identifying "our own" row by pid is fragile | Medium: our lock treated as external (kill instead of clean stop) | Compare against `self.proc.pid` while alive; if `self.proc` is None, all rows are external by definition | open |
| Feature grows the one-file app / `CLAUDE.md` invariant drifts | Low-Medium: maintainability | Keep single-file; update `CLAUDE.md` to the narrowed D17 source-of-truth model as part of Phase 4 | open |
| Scope creep pulls back the lease/CLI/watchdog machinery or the macOS port | Low: wasted effort rebuilding logind | Reset note + retired phases document why they are out; D9 keeps macOS out | open |

## Retired Risks (old lease architecture)

Kept for history; no longer relevant under the logind-dashboard model.

- Daemon down when an agent dies → stale lease lingers. (No lease files exist.)
- PID reuse makes a dead lease look alive. (No PID-based liveness; logind owns cleanup.)
- Agent gives no liveness signal → lease never expires. (No leases.)
- User quits tray with agents working → silent loss of protection. (Quit drops only our own lock; external holders survive — reshaped, see `tray-ux.md`.)
- Tray reads a half-written lease file. (No lease files.)
- Clock change / future mtime causes spurious release. (No mtime-based staleness.)
