# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Sodamint is a GTK3 system-tray toggle that keeps a Linux machine awake. It is a
caffeine analog for Linux Mint / Kubuntu. The entire app is one file:
`sodamint.py` (~200 lines). There is no build step, no test suite, no
dependency manifest.

## Running & installing

```bash
python3 sodamint.py          # run directly from the checkout
./install.sh                 # install into ~/.local + enable login autostart
./install.sh --no-autostart  # install without autostart
./install.sh --uninstall     # remove everything install.sh created
```

Runtime dependencies (system packages, not pip):
`python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1`, plus `systemd`.
`install.sh check_deps()` probes for these and warns before installing.

## How it works (the one non-obvious thing)

Keep-awake is not done via xdg-screensaver/DPMS — that's exactly what the
classic `caffeine` uses and what fails here. Instead `start()` spawns a
long-lived subprocess:

```
systemd-inhibit --what=idle:sleep --why=... --mode=block sleep infinity
```

The running process *is* the lock. `stop()` releases it by `terminate()`-ing
that subprocess. So `self.proc` (the `subprocess.Popen` handle) is the single
source of truth for on/off state — `is_on()` checks `proc is not None and
proc.poll() is None`, and everything else derives from it.

## Architecture notes

- **One class, `Sodamint`.** Constructor picks the tray backend, `_build_menu()`
  builds the GTK menu, the `start`/`stop`/`toggle`/`is_on` block manages the
  inhibitor process, and `_refresh()` is the single place that repaints all UI
  (icon, checkbox, status label) from `is_on()`. When adding UI state, update
  `_refresh()` rather than mutating widgets ad hoc.
- **Two tray backends, chosen at runtime.** AppIndicator (Ayatana first, then
  legacy `AppIndicator3`) is preferred; if neither imports, it falls back to
  `Gtk.StatusIcon`. Any code touching the tray must handle both `self.indicator`
  (AppIndicator path) and `self.status_icon` (fallback path) — see the branches
  in `_refresh()`.
- **External death is handled.** `GLib.child_watch_add` → `_on_child_exit`
  resets `self.proc` if the inhibitor is killed outside the app, so the UI stays
  truthful. Preserve this if you touch process lifecycle.
- **Checkbox feedback loop guard.** `_refresh()` blocks the `toggled` handler
  (`handler_block_by_func`) while setting the checkbox, so programmatic updates
  don't re-trigger `start()`/`stop()`.

## Icons

`icons/sodamint-active.svg` / `sodamint-inactive.svg` are installed into the
hicolor status theme and referenced by name only (`ICON_ACTIVE` /
`ICON_INACTIVE` = `sodamint-active` / `sodamint-inactive`). Running from the
checkout without installing means the theme can't resolve those names, so the
tray icon may be blank until `install.sh` has run.
