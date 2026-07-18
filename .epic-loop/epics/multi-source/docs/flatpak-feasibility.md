# Flatpak Build — Feasibility, Requirements, and Whether to Adapt Now

## Question

Should Sodamint ship as a Flatpak on Flathub? This doc records what that would
take and the one code change it is gated on. **Verdict: feasible, but NOT
adapted now (D22) — gated on moving keep-awake off the `systemd-inhibit`
subprocess to a held `login1 Inhibit()` D-Bus fd.**

## The gate: keep-awake can't spawn `systemd-inhibit` in the sandbox

Sodamint keeps the machine awake today by spawning
`systemd-inhibit --what=idle:sleep … sleep infinity` and holding that
subprocess (`self.proc` is the lock; `terminate()` releases it). **Inside a
Flatpak sandbox there is no `systemd-inhibit` binary and no host-process
spawning**, so this model does not work as-is.

The supported replacement is to call logind's
`org.freedesktop.login1.Manager.Inhibit()` **D-Bus method directly** and **hold
the returned file descriptor open** for the lifetime of the lock — keeping the
fd open *is* the lock; closing it releases it. That is a real product change to
`start()`/`stop()`/`is_on()` (the lock becomes an fd, not a `Popen`), and it is
the single thing Flatpak is blocked on. See [`data-source.md`](data-source.md)
(D11): the app already talks to `login1` over D-Bus for **reading** the list, so
the plumbing and permission model are known; only the **hold** path needs the
`Inhibit()`-fd rework.

## Sandbox blockers / required changes

- **Keep-awake hold (the gate)** — replace the `systemd-inhibit` subprocess with
  a held `login1 Inhibit()` fd (as above). Main code change.
- **Reading inhibitors** — already `login1 ListInhibitors` over the **system
  bus** (D11); sandbox-friendly given the talk-name permission below. No change
  beyond the permission. (The `systemd-inhibit --list` *fallback* would be
  unavailable in-sandbox, so the D-Bus path becomes mandatory there — acceptable,
  since D-Bus is already primary.)
- **Tray** — must render via **StatusNotifierItem (SNI)** on the session bus.
  The AppIndicator/Ayatana backend already speaks SNI, so it is the path to rely
  on; the X11 `Gtk.StatusIcon` fallback does not work under a Flatpak/Wayland
  sandbox and would effectively be dropped for the Flatpak build.

## Manifest permissions (illustrative — not added now)

A finished `finish-args` would need roughly:

- `--system-talk-name=org.freedesktop.login1` — call `Inhibit()` /
  `ListInhibitors()` on the **system** bus.
- `--socket=session-bus` and StatusNotifier access (e.g.
  `--talk-name=org.kde.StatusNotifierWatcher`) — the tray.
- `--socket=wayland` and `--socket=fallback-x11` — GTK display.

These are indicative; the exact set is settled when the build is actually done.

## Flathub submission flow (when adopted)

1. **App ID** — reverse-DNS, e.g. `com.github.<owner>.Sodamint` (also the
   `.desktop`/metainfo basename).
2. **flatpak-builder manifest** — `com.github.<owner>.Sodamint.yaml` (or JSON):
   runtime (`org.gnome.Platform`), the `finish-args` above, and a module that
   installs the single `sodamint.py` + launcher + icons + `.desktop` (the same
   file map as `packaging/`).
3. **AppStream metadata** — a `metainfo.xml` (summary, description, screenshots,
   license) plus the existing `sodamint.desktop`.
4. **Local test** — `flatpak-builder --install --user build-dir <manifest>` then
   run; confirm the tray shows and keep-awake holds via the `Inhibit()` fd.
5. **Submit** — open a PR adding the manifest to the `flathub/flathub` repo;
   Flathub reviews and, once merged, builds and hosts it.

## Recommendation / decision

**Do not adapt now (D22).** Flatpak is feasible and the distribution win (Flathub
+ sandboxed install) is real, but it is **gated on the `Inhibit()`-fd change** to
keep-awake — until `start()`/`stop()` hold a logind `Inhibit()` fd instead of a
`systemd-inhibit` subprocess, a Flatpak build cannot keep the machine awake. Keep
this note as the plan; revisit when there is a concrete reason to ship on
Flathub, starting with the fd rework (cross-ref [`data-source.md`](data-source.md)
D11) and then the manifest above.

## Sources

- Flatpak sandbox permissions / `finish-args`, `--system-talk-name` —
  https://docs.flatpak.org/en/latest/sandbox-permissions.html
- StatusNotifierItem tray under Flatpak —
  https://docs.flatpak.org/en/latest/desktop-integration.html
- logind `Inhibit()` returns a held fd —
  https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.login1.html
- Flathub submission process —
  https://docs.flathub.org/docs/for-app-authors/submission
