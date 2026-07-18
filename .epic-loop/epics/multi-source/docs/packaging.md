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

## Publishing a GitHub Release

**This is a maintainer step, run by a human — not the agent.** It needs a
configured GitHub remote (`git remote add origin …`) and `gh auth login`. The
implementation loop never runs these; it only prepares the artifact and notes.

Version/tag for the first release is **`v0.1.0`** (matches `VERSION=0.1.0` in
`packaging/build-deb.sh` and the artifact name `sodamint_0.1.0_all.deb`).

```bash
# 1. build the artifact
packaging/build-deb.sh                       # -> dist/sodamint_0.1.0_all.deb

# 2. tag the release commit and push the tag
git tag v0.1.0
git push origin v0.1.0

# 3. create the GitHub Release and upload the .deb
gh release create v0.1.0 dist/sodamint_0.1.0_all.deb \
  --title "Sodamint v0.1.0" \
  --notes "$(...)"                              # paste the notes draft below
```

(Or save the draft below to a file and use `--notes-file <that-file>`.)

Users then download `sodamint_0.1.0_all.deb` from the Releases page and
`sudo apt install ./sodamint_0.1.0_all.deb` (see the repo `README.md`).

### v0.1.0 release notes (draft)

Paste as the `--notes` body (or save to a file for `--notes-file`):

> **Sodamint v0.1.0 — first packaged release.**
>
> - **Inhibitor dashboard** — the tray lists every process holding the machine
>   awake (idle/sleep), read from systemd-logind, with who / why / pid.
> - **Manual keep-awake toggle** — one click holds your own
>   `systemd-inhibit` lock; the tray icon is active whenever *any* source exists.
> - **Agent highlighting** — inhibitors set with `--who=sodamint-agent` are
>   highlighted and grouped first (see `AGENTS.md`).
> - **Read-only external sources** — Sodamint never drops another process's lock;
>   *Disable and quit* releases only your own.
> - **Install** — `sudo apt install ./sodamint_0.1.0_all.deb`
>   (`Architecture: all`, apt-resolved GTK/AppIndicator/systemd deps).

## Next

A Launchpad PPA how-to (`docs/publishing-ppa.md`) and a Flatpak
feasibility note (`docs/flatpak-feasibility.md`) are the documented-only tasks 4
and 5.
