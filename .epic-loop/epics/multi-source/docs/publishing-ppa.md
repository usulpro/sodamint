# Publishing Sodamint on a Launchpad PPA (how-to)

A step-by-step guide for **later** publishing Sodamint to a Launchpad PPA so
users can `apt install sodamint` and get updates. **Nothing here is set up yet —
this is a future, manual procedure.** The direct-download `.deb`
(`packaging/build-deb.sh`, see [`packaging.md`](packaging.md)) is unchanged and
stays as-is for one-off installs; a PPA additionally needs a Debian **source**
package that Launchpad builds itself.

Replace `<owner>` with your Launchpad username and `<version>` with the release
version (e.g. `1.0.0`) throughout.

## 1. Prerequisites (one-time)

- A **Launchpad account** — https://launchpad.net.
- A **GPG key**, registered on your Launchpad profile. Launchpad accepts uploads
  only when the `.changes` is signed by a key it knows.
  ```bash
  gpg --full-generate-key                 # if you don't have one
  gpg --list-secret-keys --keyid-format long
  gpg --send-keys <KEYID>                 # publish to a keyserver
  # then add the key fingerprint at https://launchpad.net/~<owner>/+editpgpkeys
  ```
- An **SSH key** on your Launchpad profile (for `dput` over sftp, if used).
- Tooling on your build machine:
  ```bash
  sudo apt install devscripts debhelper dput dput-ng
  ```

## 2. Turn the package into a Debian *source* package

The binary recipe (`packaging/build-deb.sh`) uses `dpkg-deb` directly — fine for
a downloadable `.deb`, but a PPA needs a source package built with `debuild -S`
and a `debian/` control tree. Create a `debian/` directory mirroring the current
file map and dependencies (from [`packaging.md`](packaging.md)):

- **`debian/control`** — a Source stanza plus a Binary stanza:
  ```
  Source: sodamint
  Section: utils
  Priority: optional
  Maintainer: Oleg Proskurin <usulpro@gmail.com>
  Build-Depends: debhelper-compat (= 13)
  Standards-Version: 4.6.2
  Homepage: https://github.com/<owner>/sodamint

  Package: sodamint
  Architecture: all
  Depends: ${misc:Depends}, python3-gi, gir1.2-gtk-3.0,
           gir1.2-ayatanaappindicator3-0.1, systemd
  Description: Tray toggle + dashboard that keeps a Linux machine awake
   Sodamint holds a systemd-logind idle/sleep inhibitor to keep the machine
   awake and shows a live read-only dashboard of every process holding it awake.
  ```
  (Same `Depends` set as `install.sh check_deps` / the binary `.deb`; keep them
  in lockstep.)
- **`debian/changelog`** — the version and **target Ubuntu series** (Launchpad
  builds per series). Use `dch --create`:
  ```
  sodamint (<version>~noble1) noble; urgency=medium

    * Initial PPA release.

   -- Oleg Proskurin <usulpro@gmail.com>  <RFC-2822 date>
  ```
  The `~noble1` suffix targets 24.04 (noble); repeat with `~jammy1`/`jammy`, etc.
  for other series (see §6).
- **`debian/rules`** — a minimal dh file:
  ```make
  #!/usr/bin/make -f
  %:
  	dh $@
  ```
  (Tab-indented.) `install`/data placement is declared below.
- **`debian/install`** — map the repo files to their system paths (mirrors the
  binary layout):
  ```
  sodamint.py                    usr/share/sodamint
  icons/sodamint-active.svg      usr/share/icons/hicolor/scalable/status
  icons/sodamint-inactive.svg    usr/share/icons/hicolor/scalable/status
  sodamint.desktop               usr/share/applications
  ```
  The `/usr/bin/sodamint` launcher can be shipped via a `debian/sodamint.links`
  or a small file installed the same way (`exec python3
  /usr/share/sodamint/sodamint.py "$@"`).
- **`debian/source/format`** — `3.0 (native)` (Sodamint has no separate upstream
  tarball) or `3.0 (quilt)` if you split upstream vs packaging.
- **`debian/postinst` / `debian/postrm`** (optional) — the same
  `gtk-update-icon-cache` / `update-desktop-database` refresh as the binary
  recipe; `debhelper` also generates these automatically for icon/desktop dirs.

## 3. Build the signed source package

From the source tree (with `debian/` present):

```bash
debuild -S -sa          # -S = source only; -sa = include the .orig if applicable
```

`debuild` signs the `.dsc` and `.changes` with your GPG key. Output (in the
parent dir): `sodamint_<version>~noble1.dsc`, `..._source.changes`, and the
tarball. Fix any `lintian` complaints it reports before uploading.

## 4. Upload to the PPA

- Create the PPA once on Launchpad: your profile → **Create a new PPA** (e.g.
  named `sodamint`).
- Upload the signed source changes:
  ```bash
  dput ppa:<owner>/sodamint ../sodamint_<version>~noble1_source.changes
  ```
- Launchpad verifies the signature, **builds the binary itself** on its builders,
  and emails you success or failure. Built packages appear at
  `https://launchpad.net/~<owner>/+archive/ubuntu/sodamint`.

## 5. End-user install flow

Once the PPA has built packages, users install with:

```bash
sudo add-apt-repository ppa:<owner>/sodamint
sudo apt update
sudo apt install sodamint
```

Updates then arrive through normal `apt upgrade`.

## 6. Version & series notes

- **One upload per Ubuntu series.** Give each a series-suffixed version
  (`<version>~noble1`, `<version>~jammy1`, …) and the matching series name in the
  `changelog` line; upload each with `dput`.
- **Bumping the version:** `dch -v <new-version>~<series>1`, describe the change,
  rebuild with `debuild -S`, and `dput` again. Launchpad rejects re-uploads of an
  already-used version, so always increment.
- Keep the `Depends` in `debian/control` in lockstep with `install.sh check_deps`
  and `packaging/build-deb.sh` — all three list the same runtime packages.

---

*This document is a plan. No `debian/` tree, source package, PPA, or upload
exists yet; create them by following the steps above when publishing is desired.*
