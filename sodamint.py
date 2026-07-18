#!/usr/bin/env python3
"""
Sodamint — a caffeine analog for Linux Mint / Kubuntu.

Keeps the machine awake by holding a systemd-logind sleep+idle inhibitor,
which is why it works where the classic `caffeine` (xdg-screensaver / DPMS)
does not. A tray icon toggles the state on/off. Mode: stays on until you
turn it off (or quit).

Under the hood it runs exactly:
    systemd-inhibit --what=idle:sleep --why="Sodamint" --mode=block sleep infinity
and releases the lock by terminating that process.
"""

import collections
import signal
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gio, GLib, Gtk  # noqa: E402

# AppIndicator lives under different namespaces on different distros.
# Try the modern Ayatana one first, then the legacy name.
AppIndicator = None
for _ns, _ver in (("AyatanaAppIndicator3", "0.1"), ("AppIndicator3", "0.1")):
    try:
        gi.require_version(_ns, _ver)
        AppIndicator = getattr(__import__("gi.repository", fromlist=[_ns]), _ns)
        break
    except (ValueError, ImportError):
        continue

APP_ID = "sodamint"
INHIBIT_WHAT = "idle:sleep"
INHIBIT_WHY = "Sodamint keep-awake"
ICON_ACTIVE = "sodamint-active"
ICON_INACTIVE = "sodamint-inactive"

# One logind inhibitor as returned by ListInhibitors(): (what, who, why, mode,
# uid, pid). `what` is a colon list (e.g. "idle:sleep"); uid/pid are ints.
Inhibitor = collections.namedtuple("Inhibitor", "what who why mode uid pid")


def _keeps_awake(what):
    """True iff this inhibitor's `what` actually blocks idle/sleep (D12)."""
    kinds = str(what).split(":")
    return "idle" in kinds or "sleep" in kinds


def _list_inhibitors_dbus():
    """Primary path: logind ListInhibitors over the system bus via Gio.

    Returns a list of Inhibitor (unfiltered). Raises on any bus/logind error so
    the caller can fall back.
    """
    bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    res = bus.call_sync(
        "org.freedesktop.login1", "/org/freedesktop/login1",
        "org.freedesktop.login1.Manager", "ListInhibitors",
        None, GLib.VariantType("(a(ssssuu))"),
        Gio.DBusCallFlags.NONE, -1, None,
    )
    # unpack()[0] is a list of (what, who, why, mode, uid, pid) tuples.
    return [Inhibitor(*row) for row in res.unpack()[0]]


def _list_inhibitors_fallback():
    """Fallback: scrape `systemd-inhibit --list` when D-Bus is unavailable.

    Parses by the header's column offsets (WHO/UID/USER/PID/COMM/WHAT/WHY/MODE)
    so multi-word WHO/WHY fields survive. Returns [] on any failure.
    """
    try:
        out = subprocess.run(
            ["systemd-inhibit", "--list", "--no-pager"],
            capture_output=True, text=True, check=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []

    lines = out.splitlines()
    if not lines:
        return []
    header = lines[0]
    cols = ["WHO", "UID", "USER", "PID", "COMM", "WHAT", "WHY", "MODE"]
    starts = []
    for name in cols:
        idx = header.find(name)
        if idx < 0:
            return []  # unexpected format — bail to []
        starts.append(idx)
    bounds = list(zip(starts, starts[1:] + [None]))

    def field(line, i):
        s, e = bounds[i]
        return line[s:e].strip() if e is not None else line[s:].strip()

    inhibitors = []
    for line in lines[1:]:
        if not line.strip():
            continue
        try:
            uid = int(field(line, 1))
            pid = int(field(line, 3))
        except ValueError:
            continue  # legend/blank/garbage line
        inhibitors.append(Inhibitor(
            what=field(line, 5), who=field(line, 0), why=field(line, 6),
            mode=field(line, 7), uid=uid, pid=pid,
        ))
    return inhibitors


def list_inhibitors():
    """Return the live idle/sleep inhibitors as a list of Inhibitor records.

    D-Bus (login1) is the primary source; `systemd-inhibit --list` is a
    fallback. Only rows that actually keep the machine awake are kept (D12).
    Never raises: returns [] when nothing is held or the source is unreachable.
    """
    try:
        rows = _list_inhibitors_dbus()
    except Exception:
        rows = _list_inhibitors_fallback()
    return [r for r in rows if _keeps_awake(r.what)]


# Row-type glyphs shown in the tray (docs/tray-ux.md).
GLYPH = {"agent": "◆", "own": "★", "other": "●"}
AGENT_WHO = "sodamint-agent"  # the marker (docs/agent-integration.md); lockstep


def _classify(inh, own_pid):
    """Row type for an inhibitor: 'agent', 'own', or 'other' (docs/data-source.md)."""
    if inh.who == AGENT_WHO:
        return "agent"
    if own_pid is not None and inh.pid == own_pid:
        return "own"
    return "other"


def _row_label(inh, own=False):
    """Human row text: the `why` (falling back to `who`) plus pid; no age (D19)."""
    base = inh.why.strip() if (inh.why and inh.why.strip()) else inh.who
    marker = " (this)" if own else ""
    return f"{base}{marker} · pid {inh.pid}"


def _group_inhibitors(inhibitors, own_pid):
    """Ordered grouping for rendering: agents first, then everything else (D20).

    Pure — returns ``[(header, [(glyph, text), ...]), ...]`` with empty groups
    omitted, so it can be verified without a display.
    """
    agents, others = [], []
    for inh in inhibitors:
        kind = _classify(inh, own_pid)
        row = (GLYPH[kind], _row_label(inh, own=(kind == "own")))
        (agents if kind == "agent" else others).append(row)
    groups = []
    if agents:
        groups.append(("Agents", agents))
    if others:
        groups.append(("Other", others))
    return groups


def _status_text(n):
    """Status-header text for N idle/sleep sources."""
    if n == 0:
        return "Idle"
    return f"Awake — {n} source" + ("" if n == 1 else "s")


class Sodamint:
    POLL_SECONDS = 4  # how often to re-read logind's inhibitor list

    def __init__(self):
        self.proc = None  # the systemd-inhibit subprocess, or None when off
        self._menu = None
        self._last_sig = None  # last rendered menu signature (skip no-op rebuilds)

        if AppIndicator is not None:
            self.indicator = AppIndicator.Indicator.new(
                APP_ID,
                ICON_INACTIVE,
                AppIndicator.IndicatorCategory.APPLICATION_STATUS,
            )
            self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
            self.indicator.set_title("Sodamint")
        else:
            # Fallback: legacy GtkStatusIcon (works even without AppIndicator).
            self.indicator = None
            self.status_icon = Gtk.StatusIcon()
            self.status_icon.set_from_icon_name(ICON_INACTIVE)
            self.status_icon.set_tooltip_text("Sodamint")
            self.status_icon.connect("activate", lambda _i: self.toggle())
            self.status_icon.connect("popup-menu", self._on_popup)

        # Build the initial menu/icon from the live list and poll for changes.
        self._refresh()
        GLib.timeout_add_seconds(self.POLL_SECONDS, self._on_poll)

    def _on_poll(self):
        self._refresh()
        return True  # keep the timer alive

    # ---- menu ---------------------------------------------------------------
    def _build_menu(self, status, groups, on):
        """Build the whole dynamic menu: status header, grouped read-only rows,
        the manual checkbox, and Quit. Rebuilt on every content change because
        AppIndicator menus are static once set (docs/tray-ux.md)."""
        menu = Gtk.Menu()

        header = Gtk.MenuItem(label=status)
        header.set_sensitive(False)
        menu.append(header)
        menu.append(Gtk.SeparatorMenuItem())

        for group_name, rows in groups:
            gh = Gtk.MenuItem(label=group_name)
            gh.set_sensitive(False)
            menu.append(gh)
            for glyph, text in rows:
                row = Gtk.MenuItem(label=f"{glyph} {text}")
                row.set_sensitive(False)  # read-only label — inert (D14)
                menu.append(row)
            menu.append(Gtk.SeparatorMenuItem())

        # Manual toggle — set the state BEFORE connecting the handler so the
        # programmatic set_active never re-triggers start()/stop() (guard).
        self.item_toggle = Gtk.CheckMenuItem(label="Keep awake (manual)")
        self.item_toggle.set_active(on)
        self.item_toggle.connect("toggled", self._on_toggle_item)
        menu.append(self.item_toggle)

        menu.append(Gtk.SeparatorMenuItem())

        item_quit = Gtk.MenuItem(label="Quit")
        item_quit.connect("activate", self.quit)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def _apply_menu(self, menu):
        self._menu = menu
        if self.indicator is not None:
            self.indicator.set_menu(menu)

    def _on_popup(self, icon, button, time):
        self._refresh()  # show fresh data the moment the user opens the tray
        self._menu.popup(None, None, Gtk.StatusIcon.position_menu,
                         icon, button, time)

    # ---- toggling -----------------------------------------------------------
    def _on_toggle_item(self, item):
        # Sync with the checkbox state chosen by the user.
        if item.get_active():
            self.start()
        else:
            self.stop()

    def toggle(self):
        if self.is_on():
            self.stop()
        else:
            self.start()

    def is_on(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self):
        if self.is_on():
            return
        try:
            self.proc = subprocess.Popen(
                [
                    "systemd-inhibit",
                    f"--what={INHIBIT_WHAT}",
                    f"--why={INHIBIT_WHY}",
                    "--mode=block",
                    "sleep", "infinity",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            self._error("systemd-inhibit not found — is this a systemd system?")
            self.proc = None
        # Notice if the child dies unexpectedly, so the UI stays truthful.
        if self.proc is not None:
            GLib.child_watch_add(self.proc.pid, self._on_child_exit)
        self._refresh()

    def stop(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None
        self._refresh()

    def _on_child_exit(self, pid, status):
        # inhibitor process ended (e.g. killed externally) — reflect that.
        if self.proc is not None and self.proc.pid == pid:
            self.proc = None
            self._refresh()

    # ---- ui state -----------------------------------------------------------
    def _refresh(self):
        """Single repaint point: derive icon, status, and rows from the live
        logind inhibitor list. The icon is active iff ANY source exists (D13);
        the checkbox still reflects only our own lock."""
        inhibitors = list_inhibitors()
        on = self.is_on()
        own_pid = self.proc.pid if on else None
        groups = _group_inhibitors(inhibitors, own_pid)
        n = len(inhibitors)
        status = _status_text(n)
        icon = ICON_ACTIVE if n >= 1 else ICON_INACTIVE

        # Icon + tooltip are idempotent and cheap — always set.
        if self.indicator is not None:
            self.indicator.set_icon_full(icon, status)
        else:
            self.status_icon.set_from_icon_name(icon)
            self.status_icon.set_tooltip_text(f"Sodamint — {status}")

        # Rebuild the menu only when the rendered content changed, so a poll
        # that finds nothing new does not close an open menu or flicker.
        sig = (on, status, tuple((name, tuple(rows)) for name, rows in groups))
        if sig != self._last_sig:
            self._last_sig = sig
            self._apply_menu(self._build_menu(status, groups, on))

    def _error(self, msg):
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Sodamint",
        )
        dialog.format_secondary_text(msg)
        dialog.run()
        dialog.destroy()

    # ---- lifecycle ----------------------------------------------------------
    def quit(self, *_):
        self.stop()
        Gtk.main_quit()


def main():
    # Allow Ctrl+C to kill it cleanly when run from a terminal.
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = Sodamint()
    try:
        Gtk.main()
    finally:
        app.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
