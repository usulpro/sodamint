# Risk Register

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Daemon down when an agent dies → stale lease lingers | Low: no inhibitor is held while the daemon is down, so the machine can still sleep; file is just inert | Startup reconciliation prunes dead leases before re-acquiring the lock; tmpfs wipe on reboot | open |
| PID reuse makes a dead lease look alive | Medium: machine kept awake with no real work | Record process start-time at acquire; watchdog treats mismatched start-time as dead; watch-file/heartbeat are independent catches | open |
| Agent gives no liveness signal (`--pid 0`, no watch/heartbeat) | Medium: lease never auto-expires | `list`/tray flag "no liveness"; default keeps PID liveness on; document that detached work must pass `--watch`/heartbeat | open |
| User quits tray with agents working → silent loss of protection | Medium: machine sleeps mid-session | Quit confirms when leases are active; leases left on disk so restart resumes | open |
| Tray reads a half-written lease file | Low: transient bad state / crash | Atomic write (temp + rename); daemon skips unparseable files (readJsonSafe) | open |
| AppIndicator menu is static; dynamic lease list won't update | Medium: tray shows stale list | `_refresh()` rebuilds the menu and re-applies via `set_menu()`; verify on both AppIndicator and StatusIcon backends | open |
| Clock change / future mtime causes spurious release | Low: a valid lease dropped | Clamp ages/staleness at zero; treat future timestamps as "now" | open |
| Scope creep pulls in the macOS port | Low: wasted effort | D9 records "do not port"; port is explicit non-scope | open |
| Feature grows the one-file app / CLAUDE.md invariant drifts | Low-Medium: maintainability | Keep single-file; update CLAUDE.md to the lease-set source-of-truth model as part of the work | open |
