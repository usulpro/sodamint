# Packaging — building the .deb

How Sodamint is packaged into an installable Debian package. The clean-env
install test is a separate step (Phase 5 task 2); this doc covers building the
artifact.

## Build

```bash
packaging/build-deb.sh            # writes dist/sodamint_<version>_all.deb
packaging/build-deb.sh /some/dir  # or into a chosen output dir
```

Needs only `dpkg-deb` (base `dpkg`) — no `debuild`, `fpm`, or `lintian`. The
script stages a file tree, writes `DEBIAN/control` + `postinst`/`postrm`, and
packs it with `dpkg-deb --build --root-owner-group`.

## Version

`Architecture: all` (pure Python + data, no compiled code). The version lives in
one place — `VERSION=` at the top of `packaging/build-deb.sh`. Bump it there for
a new release; the output filename and the control `Version:` follow it.

## Installed file layout (system-wide)

Mirrors `install.sh`, but under `/usr` instead of `~/.local`:

| Source | Installed path | Mode |
| --- | --- | --- |
| `sodamint.py` | `/usr/share/sodamint/sodamint.py` | 0644 |
| (generated launcher) | `/usr/bin/sodamint` | 0755 |
| `icons/sodamint-active.svg` | `/usr/share/icons/hicolor/scalable/status/sodamint-active.svg` | 0644 |
| `icons/sodamint-inactive.svg` | `/usr/share/icons/hicolor/scalable/status/sodamint-inactive.svg` | 0644 |
| `sodamint.desktop` | `/usr/share/applications/sodamint.desktop` | 0644 |

The `/usr/bin/sodamint` launcher is `exec python3 /usr/share/sodamint/sodamint.py "$@"`.

## Dependencies

```
Depends: python3-gi, gir1.2-gtk-3.0, gir1.2-ayatanaappindicator3-0.1, systemd
```

This is exactly the set `install.sh check_deps()` probes for (the GTK3 + GObject
introspection bindings, the Ayatana AppIndicator typelib, and `systemd` for
`systemd-inhibit`). Keep the two in lockstep: if `install.sh check_deps` changes,
update the `Depends:` line in `packaging/build-deb.sh` to match.

## Maintainer scripts

- `postinst` / `postrm` refresh the icon and desktp-entry caches:
  `gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor` and
  `update-desktop-database -q /usr/share/applications` (both `|| true`, mirroring
  `install.sh`).

## Artifact location

The built `.deb` lands in `dist/` (gitignored — it is a build artifact, not
source). Only the recipe (`packaging/`) and this doc are committed. Rebuild it
from source whenever it is needed (install test, GitHub Release upload).

## Inspecting the build

```bash
dpkg-deb -I dist/sodamint_<v>_all.deb   # control: Architecture: all + Depends
dpkg-deb -c dist/sodamint_<v>_all.deb   # contents: the file map above
```

## Next

The end-to-end clean-environment install test (`apt install ./…deb`, launch,
verify keep-awake, `apt remove`) is Phase 5 task 2 and may require a container or
VM. Publishing via GitHub Releases is task 3; a Launchpad PPA how-to and a
Flatpak feasibility note are the documented-only tasks 4 and 5.
