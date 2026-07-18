#!/usr/bin/env bash
# Build an installable Debian package for Sodamint (Architecture: all).
#
# Stages the same file map as install.sh — but system-wide — and packs it with
# dpkg-deb. Needs only dpkg-deb (+ the base coreutils); no debuild/fpm/lintian.
#
# Usage:
#   packaging/build-deb.sh [OUT_DIR]      # default OUT_DIR = ./dist
#
# Result: OUT_DIR/sodamint_<VERSION>_all.deb
set -euo pipefail

VERSION=1.0.0                                  # bump here for a new release

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # repo root
OUT_DIR="${1:-$SRC_DIR/dist}"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
chmod 0755 "$STAGE"   # mktemp is 0700; the package root must be world-readable

DEB="$OUT_DIR/sodamint_${VERSION}_all.deb"

# ---- stage the file tree -------------------------------------------------
install -Dm0644 "$SRC_DIR/sodamint.py"                 "$STAGE/usr/share/sodamint/sodamint.py"
install -Dm0644 "$SRC_DIR/icons/sodamint-active.svg"   "$STAGE/usr/share/icons/hicolor/scalable/status/sodamint-active.svg"
install -Dm0644 "$SRC_DIR/icons/sodamint-inactive.svg" "$STAGE/usr/share/icons/hicolor/scalable/status/sodamint-inactive.svg"
install -Dm0644 "$SRC_DIR/sodamint.desktop"            "$STAGE/usr/share/applications/sodamint.desktop"

# launcher on PATH
install -d "$STAGE/usr/bin"
cat > "$STAGE/usr/bin/sodamint" <<'EOF'
#!/usr/bin/env bash
exec python3 /usr/share/sodamint/sodamint.py "$@"
EOF
chmod 0755 "$STAGE/usr/bin/sodamint"

# ---- control metadata ----------------------------------------------------
# Depends mirrors install.sh check_deps exactly.
install -d "$STAGE/DEBIAN"
cat > "$STAGE/DEBIAN/control" <<EOF
Package: sodamint
Version: ${VERSION}
Architecture: all
Section: utils
Priority: optional
Maintainer: Oleg Proskurin <usulpro@gmail.com>
Depends: python3-gi, gir1.2-gtk-3.0, gir1.2-ayatanaappindicator3-0.1, systemd
Description: Tray toggle + dashboard that keeps a Linux machine awake
 Sodamint is a GTK3 system-tray app that holds a systemd-logind idle/sleep
 inhibitor to keep the machine awake, and shows a live read-only dashboard of
 every process currently holding it awake (agents highlighted). A caffeine
 analog for Linux Mint / Kubuntu.
EOF

# refresh icon + desktop caches after install/removal (mirrors install.sh)
cat > "$STAGE/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor 2>/dev/null || true
update-desktop-database -q /usr/share/applications 2>/dev/null || true
EOF
chmod 0755 "$STAGE/DEBIAN/postinst"

cat > "$STAGE/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor 2>/dev/null || true
update-desktop-database -q /usr/share/applications 2>/dev/null || true
EOF
chmod 0755 "$STAGE/DEBIAN/postrm"

# ---- build ---------------------------------------------------------------
mkdir -p "$OUT_DIR"
dpkg-deb --build --root-owner-group "$STAGE" "$DEB"

echo "Built: $DEB"
