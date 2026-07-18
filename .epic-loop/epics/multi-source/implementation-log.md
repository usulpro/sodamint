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
