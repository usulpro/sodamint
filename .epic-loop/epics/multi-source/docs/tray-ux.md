# Tray UX Decision

> **Reshaped 2026-07-17.** Rows come from logind's live inhibitor list, not from
> a lease store. External sources are **read-only** (Sodamint never drops another
> process's lock — D14); the only control is our own manual toggle. Agent-set
> inhibitors (`who=sodamint-agent`) are visually highlighted. See
> `decision-log.md` (D10–D18), [`data-source.md`](data-source.md), and
> [`agent-integration.md`](agent-integration.md).

## Goal

Turn the tray from a boolean toggle into a live view of **who is holding the
machine awake**, while keeping the one-click manual use that exists today. The
data behind every row is logind's inhibitor registry — Sodamint is the window
onto it, not the accountant.

## Icon state

The icon is **active** whenever ≥1 idle/sleep inhibitor exists (from *any*
process, D13), and **inactive** when none do. Sodamint's own manual toggle is no
longer special — it is one inhibitor among the others. This makes the tray icon
a truthful "is anything keeping this machine awake?" light.

## Menu layout

```
┌────────────────────────────────────────────┐
│ Awake — 3 sources                     (hdr) │   status header, insensitive
├────────────────────────────────────────────┤
│ ★ Sodamint keep-awake (this) · pid 5591     │   our own lock — distinct row
├────────────────────────────────────────────┤
│ Agents                                (hdr) │   group header, insensitive
│ ◆ epic-loop · sodamint · Phase 2 · pid 48213│   agent source
│ ◆ nightly-build · sodamint · pid 49780      │
├────────────────────────────────────────────┤
│ System  (2)                         ▸       │   submenu → opens a flyout:
│                              ┌──────────────────────────────┐
│                              │ ● GNOME Shell · pid 2210     │
│                              │ ● NetworkManager · pid 933   │
│                              └──────────────────────────────┘
├────────────────────────────────────────────┤
│ ☑ Keep awake (manual)                       │   manual toggle (checkbox)
│ ☐ Start on login                            │   per-user autostart (checkbox)
├────────────────────────────────────────────┤
│ Disable and quit                            │   dynamic label (toggle is on)
└────────────────────────────────────────────┘
```

- **Status header** — `Awake — N sources` or `Idle` when empty. Insensitive
  (label only). The count is always the full total, even while System is
  collapsed.
- **Our own lock is its own row** — when the manual toggle is on, our `★` lock
  is shown as a standalone, visually distinct row (never inside the System list),
  so it is obvious which lock is ours to drop.
- **Agents** — agent sources (`who == sodamint-agent`) under an insensitive
  `Agents` header (D20). Shown only when non-empty.
- **System (submenu)** — all other (non-agent, non-ours) inhibitors live in a
  native **submenu** under a `System  (k)` item; hovering/clicking it opens a
  flyout with the `●` rows, keeping the top level compact. The `(k)` count shows
  on the parent. A submenu is used rather than an in-place collapse because tray
  menus close on item activation (the panel controls this for AppIndicator), so
  an accordion would force a reopen; a submenu flyout stays open natively. Shown
  only when there is at least one such source.
- **One row per inhibitor** — a marker glyph, the `why` string (falling back to
  `who` when empty), and the pid. **No age column** (D19). Source rows are
  **read-only labels** — no per-source release (D14). Glyphs:
  - `◆` **agent source** — `who == sodamint-agent` (see
    [`agent-integration.md`](agent-integration.md)); grouped under `Agents`.
  - `★` **our own manual lock** — pid matches `self.proc`; its own distinct row.
  - `●` **any other inhibitor** — arbitrary system/app source; under `System`.
- **Keep awake (manual)** — the classic checkbox, the primary control. Checking
  it starts our own `systemd-inhibit … sleep infinity` subprocess (today's
  `start()`); unchecking terminates it (`stop()`). This is unchanged from today
  and is how the user releases the one lock Sodamint owns. The feedback-loop
  guard (state set before the handler is connected) is kept.
- **Start on login** — a checkbox that creates/removes a per-user autostart
  entry at `~/.config/autostart/sodamint.desktop` (respecting `XDG_CONFIG_HOME`).
  The `.deb`/PPA packages install the app + its menu launcher but do **not**
  enable autostart, so this is the install-agnostic way to run Sodamint at login;
  it writes the same file `install.sh` seeds. The checkbox reflects whether that
  file exists; its `Exec=` prefers the `sodamint` launcher on `PATH`, falling
  back to the running interpreter + script. Same guard as above.
- **Quit item** — see below; its label is dynamic.

## No release of external sources (D14)

logind has **no API to release another process's inhibitor** — the lock is an fd
owned by the holder — and killing the holder was rejected as too blunt. So the
tray offers **no drop action for external sources**; they are display-only. The
only lock the tray releases is our own manual one, via the checkbox above (or by
quitting). To stop an external source the user acts on that process directly,
outside Sodamint.

## Both tray backends

The dynamic list must render on both paths described in `CLAUDE.md`: the
AppIndicator path (`self.indicator`) and the `Gtk.StatusIcon` fallback
(`self.status_icon` + `self._menu`). Because AppIndicator menus are static once
set, `_refresh()` **rebuilds** the inhibitor section (or resets the whole menu)
rather than mutating labels in place, and re-applies it via `set_menu()`.
`_refresh()` stays the single place that repaints all UI from the current
inhibitor list.

## Refresh triggers

logind emits no "inhibitor added/removed" signal, so `_refresh()` runs on:
(a) a `GLib.timeout` poll of `ListInhibitors()` every few seconds, and (b) when
the menu is popped up (so a user opening the tray sees fresh data immediately).
Rows carry no age (D19), so the poll cadence alone is enough — no per-second timer.

## Quit behavior (D21)

Quitting Sodamint stops **only our own** `systemd-inhibit` subprocess. Every
external inhibitor is a separate process that keeps running and keeps holding
its own lock — so **quitting does not put the machine to sleep** if agents are
still working. This is strictly safer than the old lease design, where quit
dropped the single shared lock.

There is **no confirmation dialog**. Instead the Quit menu item's **label is
dynamic**, so it tells the truth about what quitting will do:

- Manual toggle **off** → label `Quit` — nothing of ours to drop; quit
  immediately.
- Manual toggle **on** → label `Disable and quit` — quitting will release our
  own keep-awake lock (our subprocess is terminated on exit). External sources
  are unaffected either way.

`_refresh()` updates this label from `is_on()` alongside the icon and checkbox
(single repaint point). Quit action itself is unchanged: `stop()` then
`Gtk.main_quit()`.

## Non-goals for the UI

- No control over external sources at all — no release, no kill, no edit. They
  are read-only labels (D14).
- No per-source styling beyond the three row-type glyphs (`◆`/`★`/`●`).
- No history of ended sources in the menu (that is log territory, not tray).
- No re-creating logind's bookkeeping — the tray reflects logind, it does not
  cache or reconcile state of its own.
