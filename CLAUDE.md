# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Sodamint is a GTK3 system-tray app that keeps a Linux machine awake **and**
shows a live dashboard of everything currently holding it awake. It is a
caffeine analog for Linux Mint / Kubuntu. The entire app is one file:
`sodamint.py`. There is no build step, no test suite, no dependency manifest.

The tray is a window onto systemd-logind's inhibitor registry: every idle/sleep
source (who/why/pid) is listed read-only, agent-set sources are highlighted, and
the one thing you can control is your own manual keep-awake toggle.

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

## How it works (the two non-obvious things)

**1. Our own keep-awake is a subprocess, not DPMS.** Keep-awake is not done via
xdg-screensaver/DPMS — that's exactly what the classic `caffeine` uses and what
fails here. Instead `start()` spawns a long-lived subprocess:

```
systemd-inhibit --what=idle:sleep --why=... --mode=block sleep infinity
```

The running process *is* the lock. `stop()` releases it by `terminate()`-ing
that subprocess. So `self.proc` (the `subprocess.Popen` handle) is the source of
truth **only for our own manual lock** — `is_on()` checks `proc is not None and
proc.poll() is None`, and the checkbox derives from it.

**2. The tray reflects logind, not just us.** `list_inhibitors()` reads the full
idle/sleep inhibitor list from logind — `login1 ListInhibitors` over the system
bus via `Gio` (primary), falling back to parsing `systemd-inhibit --list`, both
filtered to holders that actually block idle/sleep (D12). The tray **icon is
active whenever ANY source exists**, not just ours, so it is a truthful "is
anything keeping this machine awake?" light. External sources are **read-only**
(D14) — Sodamint never drops another process's lock; logind offers no API to,
and the only lock we release is our own. See the epic docs under
`.epic-loop/epics/multi-source/docs/` for the full design.

## Architecture notes

- **One class, `Sodamint`.** Constructor picks the tray backend, the
  `start`/`stop`/`toggle`/`is_on` block manages our own inhibitor process, and
  `_refresh()` is the single place that repaints all UI from the live inhibitor
  list. When adding UI state, update `_refresh()` rather than mutating widgets ad
  hoc.
- **`_refresh()` repaints from `list_inhibitors()`.** It sets the icon from the
  block-holder *count* (active iff ≥1), a status header (`Awake — N sources` /
  `Idle`), and read-only rows. `list_inhibitors()` returns **every** idle/sleep
  holder (block + delay) so the dashboard shows the full picture; the icon/status
  count only **`mode == "block"`** holders — the ones that actually keep the
  machine awake — so ever-present `delay`-mode hooks (NetworkManager,
  ModemManager, "cleanup before suspend", …) still show in `System` but don't pin
  the icon active (`Idle` + a non-empty `System (k)` is normal). All rows come
  from the live logind list (single source of truth): `_partition_inhibitors()`
  splits it into our own lock (`★`, matched by `self.proc.pid`) as its **own
  distinct, always-present row** (a blank line holds the slot when not held, so
  toggling only changes the row's label — never the item count — keeping the menu
  height fixed so the open menu doesn't scrunch into scroll arrows), agent
  sources (`◆`,
  `who == "sodamint-agent"`) under an `Agents` header, and everything else (`●`)
  in a native **`System (k)` submenu** (a flyout, since tray menus close on item
  activation and can't do an in-place accordion). It also drives the keep-awake
  checkbox (from `is_on()`), the **`Start on login`** checkbox (from
  `_autostart_enabled()` — a per-user `~/.config/autostart/sodamint.desktop` the
  packages don't ship), and the
  **dynamic Quit label** (`Disable my keep-awake & quit` when our lock is on,
  else `Quit` — "my" because quit drops only our lock, never agent/external ones,
  so the machine can stay awake after we exit).
  Source rows are inert (no per-source action — D14). Refreshes run on a
  `GLib.timeout_add_seconds(POLL_SECONDS, …)` poll and on StatusIcon popup
  (logind emits no inhibitor-changed signal).
- **The menu is rebuilt, not mutated.** AppIndicator menus are static once set,
  so `_refresh()` rebuilds the whole menu via `_build_menu(status, groups, on)`
  and re-applies it (`indicator.set_menu()` / `self._menu`). A change-signature
  guard (`self._last_sig`) skips no-op rebuilds so polling doesn't flicker or
  close an open menu.
- **Two tray backends, chosen at runtime.** AppIndicator (Ayatana first, then
  legacy `AppIndicator3`) is preferred; if neither imports, it falls back to
  `Gtk.StatusIcon`. Any code touching the tray must handle both `self.indicator`
  (AppIndicator path) and `self.status_icon` (fallback path).
- **External death is handled.** `GLib.child_watch_add` → `_on_child_exit`
  resets `self.proc` if our inhibitor is killed outside the app, so the UI stays
  truthful. `stop()` removes that watch source (`self._child_watch`) before
  reaping so GLib doesn't `waitid()` an already-reaped pid. Preserve both if you
  touch process lifecycle.
- **Checkbox feedback loop guard.** Because the menu is rebuilt each change, the
  checkbox's state is set **before** its `toggled` handler is connected in
  `_build_menu()`, so programmatic updates never re-trigger `start()`/`stop()`.
- **Agent contract.** Agents keep the machine awake with their own
  `systemd-inhibit --who=sodamint-agent …`; Sodamint highlights those rows. The
  repo-level contract lives in `AGENTS.md` (source of truth:
  `.epic-loop/epics/multi-source/docs/agent-integration.md`); keep the
  `AGENT_WHO` marker in `sodamint.py` in lockstep with it.

## Icons

`icons/sodamint-active.svg` / `sodamint-inactive.svg` are installed into the
hicolor status theme and referenced by name only (`ICON_ACTIVE` /
`ICON_INACTIVE` = `sodamint-active` / `sodamint-inactive`). Running from the
checkout without installing means the theme can't resolve those names, so the
tray icon may be blank until `install.sh` has run.
