# Sodamint

A GTK3 system-tray app that keeps a Linux machine awake **and** shows a live
dashboard of everything currently holding it awake. It holds a systemd-logind
`idle:sleep` inhibitor (which is why it works where the classic `caffeine`
—xdg-screensaver/DPMS— does not), and lists every idle/sleep source
(who / why / pid) read-only, highlighting agent-set sources. A caffeine analog
for Linux Mint / Kubuntu.

## Install

### From a release `.deb` (recommended)

Download `sodamint_<version>_all.deb` from the
[Releases page](../../releases) and install it:

```bash
sudo apt install ./sodamint_0.1.0_all.deb
```

`apt` pulls the runtime dependencies automatically
(`python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-ayatanaappindicator3-0.1`, `systemd`).
Then launch **Sodamint** from your menu, or run `sodamint`.

To remove: `sudo apt remove sodamint`.

### From source

Run it straight from the checkout:

```bash
python3 sodamint.py
```

Or install into your user account (no root) with autostart on login:

```bash
./install.sh                 # install into ~/.local + enable login autostart
./install.sh --no-autostart  # install without autostart
./install.sh --uninstall     # remove everything install.sh created
```

Runtime dependencies (system packages, not pip):

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
```

plus `systemd` (for `systemd-inhibit`).

## Using it

- Click the tray checkbox **Keep awake (manual)** to hold your own keep-awake
  lock; uncheck it to release. The menu also lists every other process keeping
  the machine awake (read-only) — agent sources are highlighted and grouped
  first.
- The icon is active whenever **anything** is keeping the machine awake, not just
  your own toggle.
- **Quit** drops only your own lock; other sources keep the machine awake, so the
  Quit item reads *Disable and quit* while your lock is on.

## Keep-awake from an agent / script

Automated agents can keep the machine awake for the duration of their work and
show up as a highlighted source — see [`AGENTS.md`](AGENTS.md) for the one-liner
and contract.

## Building & packaging

Contributors: see [`CLAUDE.md`](CLAUDE.md) for architecture and
`.epic-loop/epics/multi-source/docs/packaging.md` for how the `.deb` is built and
released.
