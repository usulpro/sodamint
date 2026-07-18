# Implementation Log

## 2026-07-14T10:21:11+00:00 - Epic Workspace Initialized

- Created epic workspace for `multi-source`.
- Initial mode: shaping.

## 2026-07-17 - Strategic Reset (architecture-reset, shaping)

- Trigger: a prior design session (Claude Code transcript `e7c91d0e`, folder
  `sodamint/Sodamint`) concluded the lease/refcount/watchdog service is ~80%
  redundant with `systemd-inhibit`/logind — multi-source, reference counting,
  "who holds it", and crash cleanup (fd closed on holder death) are all native.
  That analysis was absent when Phase 1 first shaped the epic.
- User decision: do not rebuild what logind provides. Reshape Sodamint into a
  thin **tray UI over logind's inhibitor list** — show idle/sleep sources
  (who/why/pid) and allow manual drop. No lease store, CLI, in-app refcount, or
  watchdog.
- Artifacts reshaped: `decision-log.md` (D10–D17 supersede D1–D8; D9 kept),
  `docs/problem-framing.md`, `docs/tray-ux.md`, new `docs/data-source.md`,
  `tracker.md` (4-phase roadmap; old phases retired), `risk-register.md`,
  `state-of-epic.md`. `docs/cli-reference.md` and `docs/watch-mode.md` marked
  superseded (kept for history). `docs/macos-feasibility.md` unchanged.
- Implementation still not started; no driver bound.

## 2026-07-17 - Refinement: read-only external sources + agent contract (shaping)

- User refined the reshaped scope:
  - **Drop the external-drop feature.** External inhibitors are display-only;
    Sodamint never signals/kills another process's holder. D14 revised from
    "SIGTERM the holder" to "read-only". The only tray control is the existing
    manual toggle, which must stay a regression-safe superset of today.
  - **Add an agent-integration contract** (new `docs/agent-integration.md`,
    D18): agents keep the machine awake by running their own
    `systemd-inhibit --what=idle:sleep --who=sodamint-agent --why="…" -- <cmd>`;
    Sodamint recognizes the `sodamint-agent` marker and highlights those rows.
    Kept as project documentation; repo-level surfacing (CLAUDE.md / AGENTS.md)
    is the Phase 4 docs task.
- Artifacts touched: `decision-log.md` (D14 revised, D18 added, open questions
  updated), `docs/tray-ux.md` (read-only rows, three-glyph classification, no
  release section), `docs/data-source.md` (row classification + own-lock-only
  release), `docs/problem-framing.md`, `tracker.md` (Phase 2 highlight; Phase 3
  → "Manual Toggle & Quit", drop task removed; Phase 4 agent-doc surfacing),
  `risk-register.md` (kill risks removed, marker-collision + toggle-regression
  added), new `docs/agent-integration.md`.
- Still shaping; implementation not started; no driver bound.

## 2026-07-17 - Open questions resolved: D19–D21 (shaping)

- User answered the three remaining open questions, now locked as decisions:
  - **D19 — no age column.** Rows show why/who/pid only.
  - **D20 — agent sources grouped first**, under `Agents`/`Other` headers, `◆`
    glyph retained.
  - **D21 — dynamic Quit label, no dialog.** `Quit` when the manual toggle is
    off, `Disable and quit` when on; label updated in `_refresh()`.
- Artifacts touched: `decision-log.md` (D19–D21 added, Open Questions now empty),
  `docs/tray-ux.md` (grouped layout, no age, dynamic quit section),
  `docs/data-source.md` (age section → "no age"), `docs/problem-framing.md`,
  `tracker.md` (Phase 2 grouping/no-age acceptance, Phase 3 dynamic-quit
  acceptance), `state-of-epic.md`.
- Design is now fully settled — no open questions. Ready for Phase 2
  implementation. Still no driver bound.

## 2026-07-17 - Added Phase 5: Packaging & Distribution (D22, shaping)

- User asked to add a packaging/distribution phase with a clear split of
  execution vs documentation:
  - **Build a `.deb`** (`Architecture: all`, apt-resolved deps) — executed.
  - **Publish via GitHub Releases** — executed (artifact + README + documented
    `gh release` step; actual publish is user-gated).
  - **Launchpad PPA** — **documented only** (`docs/publishing-ppa.md`), not set
    up now.
  - **Flatpak** — **documented only** (`docs/flatpak-feasibility.md`): list the
    requirements + code changes (holding via login1 `Inhibit()` D-Bus fd, SNI
    tray, manifest perms, Flathub flow). Do **not** adapt the app for Flatpak
    now.
- Captured as **D22** and a new **Phase 5** in `tracker.md` (2 implementation +
  1 verification + 2 documentation-only tasks). Scope/non-scope updated in
  `docs/problem-framing.md`; `state-of-epic.md` now reflects a 5-phase roadmap.
- New docs to be authored during implementation: `docs/packaging.md`,
  `docs/publishing-ppa.md`, `docs/flatpak-feasibility.md`.
- Still shaping; implementation not started; no driver bound.

## 2026-07-18 - Phase 2 Task 1: list_inhibitors() (implementation, closed)

- Added the logind read path to `sodamint.py`: `Inhibitor` namedtuple
  `(what, who, why, mode, uid, pid)`, `list_inhibitors()` (public), and helpers
  `_list_inhibitors_dbus()` (primary: `login1 ListInhibitors` via Gio system
  bus, reply `(a(ssssuu))`), `_list_inhibitors_fallback()` (scrape
  `systemd-inhibit --list --no-pager`, parsed by header column offsets so
  multi-word WHO/WHY survive), `_keeps_awake()` (D12: keep rows whose `what`
  contains `idle`/`sleep`).
- Never raises: D-Bus error funnels to the fallback; fallback failure funnels to
  `[]`. No new dependency (Gio ships with `python3-gi`). Read-only — no UI wiring
  (deferred to task 2). Existing toggle/start/stop/_refresh untouched.
- Verified on live logind (real Cinnamon session, 10 held inhibitors): filter
  drops `shutdown`/`handle-lid-switch`/`handle-power-key`; a held
  `--why=tl-verify` lock appears then disappears on kill; D-Bus and fallback
  return the identical filtered set (parity); both-sources-fail → `[]`;
  `py_compile` passes. Techlead re-verified closure independently.
- Not committed: `.claude/settings.json` (unrelated hook-install infra; kept out
  of the task commit).

## 2026-07-18 - Phase 2 Task 2: render the inhibitor dashboard (implementation, closed)

- `sodamint.py`: added pure helpers `_classify` (agent/own/other), `_row_label`
  (why→who fallback, `· pid N`, optional `(this)`, no age D19),
  `_group_inhibitors` (agents-first grouping, empty groups omitted),
  `_status_text`, plus `GLYPH` and `AGENT_WHO` constants.
- `_refresh()` is now the single repaint from `list_inhibitors()`: icon active
  iff ≥1 source from ANY process (D13); status header `Awake — N source(s)` /
  `Idle`; grouped read-only (`set_sensitive(False)`, inert D14) menu rebuilt via
  `_build_menu(status, groups, on)` + `_apply_menu()` (AppIndicator `set_menu()`
  / StatusIcon `self._menu`). A change-signature guard skips no-op rebuilds so a
  poll that finds nothing new does not flicker/close an open menu.
- Refresh triggers: `GLib.timeout_add_seconds(POLL_SECONDS=4, ...)` + `_refresh()`
  on StatusIcon popup. Checkbox state is set BEFORE connecting `toggled`, so the
  feedback guard survives every rebuild (no double start/stop).
- Out of scope kept out: Quit stays static (dynamic label is Phase 3);
  `start`/`stop`/`is_on`/`toggle`/`_on_toggle_item`/`_on_child_exit` unchanged
  (diff shows only `_refresh` reads `self.proc.pid`).
- Verified: unit helper suite (classify/glyph/label/grouping/header-omission/
  status); live AppIndicator render on the real session (`Awake — 9 sources`,
  agent `◆` grouped first, `●` others incl. a held external lock); StatusIcon
  fallback construct + inert rows + Idle state + no-double-trigger guard; real
  own-lock `★` with pid == `self.proc.pid` appearing then disappearing on
  start/stop. `py_compile` passes; no new dependency.
- Follow-up recorded in risk-register: pre-existing `waitid: No child processes`
  GLib warning from `child_watch_add` + `stop()`'s `wait()` — to reconcile in
  Phase 3, not this task.
- Not committed: `.claude/settings.json` (unrelated hook-install infra).

## 2026-07-18 - Phase 2 Task 3: end-to-end verification (verification, closed) — PHASE 2 COMPLETE

- Drove the running app in-process with a real `GLib.MainLoop` so the actual
  `POLL_SECONDS=4` timer fired (criterion 1 used no manual `_refresh`).
- Results — all 6 criteria PASS on both AppIndicator and StatusIcon backends:
  1. Poll-driven update within one interval: external lock auto-appeared as a
     `●` row + icon active at ~poll+1s, then disappeared within one interval on
     kill.
  2. Agent highlight + grouping: `◆ … p2 verify` rendered first, under `Agents`.
  3. Rows mirror logind: menu source-row pids matched `list_inhibitors()` pids
     one-to-one.
  4. Icon at zero: simulated empty (`list_inhibitors → []`) → menu shows only
     `Idle`, StatusIcon reads back `sodamint-inactive`.
  5. Both backends rendered live.
  6. Source/header rows inert (insensitive).
- No product code changed; no defects. Test inhibitors cleaned up (none left);
  no app process left running.
- Notes: live active→inactive icon flip is not observable here because the host
  always holds ≥7 real inhibitors (NetworkManager/ModemManager/UPower/code/
  slack/electron/csd-power) — covered via the simulated-empty path. The
  pre-existing `waitid` warning did not surface (no own-lock start/stop in the
  harness); still tracked for Phase 3.
- **Phase 2 (Read & Render Inhibitors) is complete.**
