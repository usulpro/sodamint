#!/usr/bin/env bash
# Sodamint installer — installs the tray app into your user (no root needed).
# Usage:
#   ./install.sh            # install + enable autostart on login
#   ./install.sh --no-autostart
#   ./install.sh --uninstall
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/sodamint"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/status"
DESKTOP_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"

AUTOSTART=1
UNINSTALL=0
for arg in "$@"; do
  case "$arg" in
    --no-autostart) AUTOSTART=0 ;;
    --uninstall)    UNINSTALL=1 ;;
    *) echo "Unknown option: $arg"; exit 1 ;;
  esac
done

uninstall() {
  echo ">> Removing Sodamint..."
  rm -f  "$BIN_DIR/sodamint"
  rm -rf "$APP_DIR"
  rm -f  "$ICON_DIR/sodamint-active.svg" "$ICON_DIR/sodamint-inactive.svg"
  rm -f  "$DESKTOP_DIR/sodamint.desktop"
  rm -f  "$AUTOSTART_DIR/sodamint.desktop"
  gtk-update-icon-cache -q -t -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
  update-desktop-database -q "$DESKTOP_DIR" 2>/dev/null || true
  echo ">> Done. (Sodamint may still be running — quit it from the tray.)"
}

check_deps() {
  local missing_cmd=() missing_py=0
  command -v systemd-inhibit >/dev/null 2>&1 || missing_cmd+=("systemd (systemd-inhibit)")
  command -v python3         >/dev/null 2>&1 || missing_cmd+=("python3")
  # GTK + AppIndicator python bindings
  if ! python3 - <<'PY' 2>/dev/null; then
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
ok = False
for ns, ver in (("AyatanaAppIndicator3","0.1"),("AppIndicator3","0.1")):
    try:
        gi.require_version(ns, ver); __import__("gi.repository", fromlist=[ns]); ok = True; break
    except Exception: pass
raise SystemExit(0 if ok else 1)
PY
    missing_py=1
  fi

  if [ "${#missing_cmd[@]}" -gt 0 ] || [ "$missing_py" -eq 1 ]; then
    echo ">> Some dependencies are missing."
    [ "${#missing_cmd[@]}" -gt 0 ] && printf '   - %s\n' "${missing_cmd[@]}"
    [ "$missing_py" -eq 1 ] && echo "   - python3-gi + GTK3 + AppIndicator bindings"
    echo
    echo "   On Linux Mint / Ubuntu / Kubuntu, install with:"
    echo "     sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1"
    echo
    read -r -p "   Continue installing anyway? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
  fi
}

do_install() {
  check_deps
  echo ">> Installing Sodamint..."
  mkdir -p "$BIN_DIR" "$APP_DIR" "$ICON_DIR" "$DESKTOP_DIR"

  install -m 0755 "$SRC_DIR/sodamint.py" "$APP_DIR/sodamint.py"
  install -m 0644 "$SRC_DIR/icons/sodamint-active.svg"   "$ICON_DIR/sodamint-active.svg"
  install -m 0644 "$SRC_DIR/icons/sodamint-inactive.svg" "$ICON_DIR/sodamint-inactive.svg"

  # launcher on PATH
  cat > "$BIN_DIR/sodamint" <<EOF
#!/usr/bin/env bash
exec python3 "$APP_DIR/sodamint.py" "\$@"
EOF
  chmod 0755 "$BIN_DIR/sodamint"

  install -m 0644 "$SRC_DIR/sodamint.desktop" "$DESKTOP_DIR/sodamint.desktop"

  if [ "$AUTOSTART" -eq 1 ]; then
    mkdir -p "$AUTOSTART_DIR"
    install -m 0644 "$SRC_DIR/sodamint.desktop" "$AUTOSTART_DIR/sodamint.desktop"
    echo ">> Autostart on login: enabled"
  fi

  gtk-update-icon-cache -q -t -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
  update-desktop-database -q "$DESKTOP_DIR" 2>/dev/null || true

  echo
  echo ">> Installed."
  echo "   Run now:        sodamint &"
  echo "   (if 'sodamint' is not found, add ~/.local/bin to PATH or log out/in)"
  echo "   Uninstall:      ./install.sh --uninstall"
}

if [ "$UNINSTALL" -eq 1 ]; then uninstall; else do_install; fi
