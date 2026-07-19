<div align="center">

<img src="blog/sodamint-hero.png" alt="Sodamint" width="720">

**Keep your Linux machine awake — and see exactly what's keeping it awake.**

A tiny GTK3 tray app for Linux Mint / Kubuntu and other systemd desktops.
A caffeine analog that actually works, plus a live dashboard of every idle/sleep
inhibitor on the system.

![platform](https://img.shields.io/badge/platform-Linux-blue) ![backend](https://img.shields.io/badge/keep--awake-systemd--logind-green) ![toolkit](https://img.shields.io/badge/UI-GTK3%20tray-informational) ![deps](https://img.shields.io/badge/deps-apt%2C%20no%20pip-lightgrey) ![license](https://img.shields.io/badge/license-MIT-brightgreen)

</div>

---

## The problem

On Linux Mint / Kubuntu the "obvious" keep-awake tools poke the wrong layer.
Classic `caffeine` and X-screensaver/DPMS tricks fight the *screensaver*, but the
machine still suspends — because modern desktops sleep through **systemd-logind**,
not the X screensaver. So your long download, backup, render, or **overnight AI
coding agent** dies when the box goes to sleep.

And when something *is* keeping the machine awake, there's usually no easy way to
see **who** and **why**.

## What Sodamint does

Sodamint holds the machine awake at the correct layer — a **systemd-logind
`idle:sleep` inhibitor** — and turns the tray into a live window onto logind's
inhibitor registry:

- 🥤 **One-click keep-awake.** Toggle *Keep awake (manual)* in the tray; the icon
  lights up while anything is holding the machine awake.
- 📋 **Live dashboard.** See every process currently blocking idle/sleep — its
  reason, and PID — read straight from logind and refreshed automatically.
- ⭐ **Your own lock is called out** as its own row, so it's always clear which
  lock is yours to drop.
- 💠 **Agent sources are highlighted** and grouped, so an overnight agent shows up
  distinctly from random system services.
- 📁 **System noise is tucked away** in a `System` submenu — visible when you want
  it, out of the way when you don't.
- 🚪 **Honest quit.** Quitting drops **only your own** lock; if agents or other
  processes are still working, the machine stays awake. The Quit item even says
  *Disable my keep-awake & quit* when it's about to release your lock.

Everything is **read-only** for other processes: Sodamint never kills or drops a
lock it doesn't own.

## Install

Grab `sodamint_1.0.0_all.deb` from the [**Releases**](../../releases) page and:

```bash
sudo apt install ./sodamint_1.0.0_all.deb
```

`apt` pulls the dependencies automatically. Then launch **Sodamint** from your
menu (or run `sodamint`). It'll sit in your tray.

Remove with `sudo apt remove sodamint`.

<details>
<summary>Run from source instead</summary>

```bash
python3 sodamint.py            # run straight from the checkout
./install.sh                   # or install into ~/.local + login autostart
./install.sh --uninstall       # undo it
```

System packages it needs:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
```

plus `systemd` (for `systemd-inhibit`), which you already have.
</details>

## Keeping awake from an agent or a service

This is the key idea: **Sodamint doesn't mediate anything.** Your agent, script,
or service keeps the machine awake by talking to **systemd directly** — Sodamint
only *reads* that state and *shows* it. Nothing has to integrate with Sodamint,
and Sodamint doesn't need to be running for keep-awake to work.

Wrap your long-running work in `systemd-inhibit`. logind holds the machine awake
while the command runs and **auto-releases when it exits** (success, crash, or
kill — nothing leaks):

```bash
systemd-inhibit --what=idle:sleep --who="sodamint-agent" \
  --why="my-agent · my-project · overnight run" --mode=block \
  -- your-command --and --its --args
```

That's it. The `--who=sodamint-agent` marker is purely cosmetic — it's what makes
Sodamint **highlight** the row. Drop the marker and it still keeps the machine
awake; it just shows as a plain system source. Full contract (fields, an explicit
hold/release variant for non-command sessions) is in [`AGENTS.md`](AGENTS.md).

Because it's all logind underneath: if the holder dies, the kernel releases the
lock automatically; multiple holders reference-count natively; and Sodamint just
mirrors whatever logind reports.

## Supported systems

Sodamint needs three things: **systemd-logind** (the keep-awake engine), **GTK3 +
python3-gi**, and a system tray that supports **StatusNotifierItem/AppIndicator**
(with a fallback to the legacy `GtkStatusIcon`).

By our assessment it should run on most modern systemd Linux desktops. Where we
expect it to be at home:

| Desktop / distro | Notes |
| --- | --- |
| **Linux Mint (Cinnamon)** | Primary target; developed and tested here. |
| **Kubuntu (KDE Plasma)** | SNI tray is native. |
| **Ubuntu (GNOME)** | Works with an AppIndicator/tray extension enabled. |
| **Other Debian/Ubuntu + systemd** | Should work given the deps above. |
| **Other systemd distros** | Likely fine with equivalent GTK3/AppIndicator packages; not specifically tested. |

The `.deb` is `Architecture: all` (pure Python + assets), so it isn't tied to a
CPU architecture. It will **not** work where there's no systemd-logind (e.g. a
plain container, or non-systemd inits).

## For contributors

The whole app is one file — [`sodamint.py`](sodamint.py). See
[`CLAUDE.md`](CLAUDE.md) for architecture and
[`.epic-loop/epics/multi-source/docs/`](.epic-loop/epics/multi-source/docs/) for
the design docs and packaging (`.deb` build, PPA and Flatpak notes).

## License

[MIT](LICENSE) © Oleg Proskurin
