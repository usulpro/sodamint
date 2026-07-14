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

import signal
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

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


class Sodamint:
    def __init__(self):
        self.proc = None  # the systemd-inhibit subprocess, or None when off

        if AppIndicator is not None:
            self.indicator = AppIndicator.Indicator.new(
                APP_ID,
                ICON_INACTIVE,
                AppIndicator.IndicatorCategory.APPLICATION_STATUS,
            )
            self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
            self.indicator.set_title("Sodamint")
            self.indicator.set_menu(self._build_menu())
        else:
            # Fallback: legacy GtkStatusIcon (works even without AppIndicator).
            self.indicator = None
            self.status_icon = Gtk.StatusIcon()
            self.status_icon.set_from_icon_name(ICON_INACTIVE)
            self.status_icon.set_tooltip_text("Sodamint — off")
            self.status_icon.connect("activate", lambda _i: self.toggle())
            self.status_icon.connect("popup-menu", self._on_popup)
            self._menu = self._build_menu()

    # ---- menu ---------------------------------------------------------------
    def _build_menu(self):
        menu = Gtk.Menu()

        self.item_toggle = Gtk.CheckMenuItem(label="Keep awake")
        self.item_toggle.set_active(False)
        self.item_toggle.connect("toggled", self._on_toggle_item)
        menu.append(self.item_toggle)

        menu.append(Gtk.SeparatorMenuItem())

        self.item_status = Gtk.MenuItem(label="Status: off")
        self.item_status.set_sensitive(False)
        menu.append(self.item_status)

        menu.append(Gtk.SeparatorMenuItem())

        item_quit = Gtk.MenuItem(label="Quit")
        item_quit.connect("activate", self.quit)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def _on_popup(self, icon, button, time):
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
        on = self.is_on()
        icon = ICON_ACTIVE if on else ICON_INACTIVE
        label = "on" if on else "off"

        if getattr(self, "item_toggle", None) is not None:
            self.item_toggle.handler_block_by_func(self._on_toggle_item)
            self.item_toggle.set_active(on)
            self.item_toggle.handler_unblock_by_func(self._on_toggle_item)
        if getattr(self, "item_status", None) is not None:
            self.item_status.set_label(f"Status: {label}")

        if self.indicator is not None:
            self.indicator.set_icon_full(icon, f"Sodamint {label}")
        else:
            self.status_icon.set_from_icon_name(icon)
            self.status_icon.set_tooltip_text(f"Sodamint — {label}")

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
