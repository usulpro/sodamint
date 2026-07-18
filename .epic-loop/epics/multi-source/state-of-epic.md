# State Of Epic

Epic: Inhibitor Dashboard For Sodamint
Slug: `multi-source`
Created: 2026-07-14T10:21:11+00:00
Mode: implementation
Active phase: Phase 5 - Packaging & Distribution (in progress)
Active task: Phase 5 task 1 (`.deb` build recipe + docs/packaging.md) done → next: task 2 (clean-env `.deb` install verification — needs container/VM or deps-purge)

## Current State

- **Strategic reset applied 2026-07-17.** A prior design session (transcript
  `e7c91d0e` in the `sodamint/Sodamint` folder) found the original
  lease/refcount/watchdog service ~80% redundant with `systemd-inhibit`/logind
  (including crash cleanup). Per user direction, the epic is now a thin **tray
  UI over logind's inhibitor list**: show every idle/sleep source (who/why/pid)
  and let the user manually drop one. No lease store, CLI, in-app refcount, or
  watchdog.
- Decisions reshaped: **D10–D21** define the new architecture and **supersede
  D1–D8**; **D9** (do not port to macOS) stands and is more central now.
  D19–D21 lock the last open questions: no age column; agents grouped first;
  dynamic Quit label (`Quit` / `Disable and quit`) instead of a dialog.
- **Refinement 2026-07-17 (same day):** external sources are now **read-only**
  — Sodamint never drops another process's lock (D14 revised; the SIGTERM-kill
  path is dropped). The only tray control is the existing manual toggle, which
  is kept strictly regression-safe. Added **D18** + `docs/agent-integration.md`:
  agents self-set a `systemd-inhibit` block tagged `--who=sodamint-agent` and
  Sodamint highlights those rows (`◆`).
- Active docs: `docs/problem-framing.md`, `docs/tray-ux.md`, `docs/data-source.md`
  (login1 D-Bus read + row classification), `docs/agent-integration.md` (new —
  agent wrapper + message-format contract), `docs/macos-feasibility.md`
  (unchanged, "do not port").
- Superseded docs kept for history with banners: `docs/cli-reference.md`,
  `docs/watch-mode.md`.
- `tracker.md` reshaped to a **5-phase** roadmap (Shape → Read&Render(+highlight)
  → Manual Toggle&Quit → Docs&E2E → Packaging&Distribution); the old
  lease/CLI/watchdog/wrapper phases are retired at the bottom.
- **Phase 5 added 2026-07-17 (D22):** build a `.deb` and publish via GitHub
  Releases; write a Launchpad PPA how-to (`docs/publishing-ppa.md`) and a
  Flatpak feasibility/requirements doc (`docs/flatpak-feasibility.md`) — PPA and
  Flatpak are documented-only, the app is **not** adapted for Flatpak now.

## Blockers

- None. **No open questions remain** — D19–D21 resolved the last three (age,
  highlight style, quit), and the external-drop questions are moot under D14.
  The design is fully settled and ready to implement.

## Next Action

- Scope and all decisions are settled; ready to move to implementation starting
  at Phase 2 (read & render inhibitors from logind).
- Implementation is NOT started; no session is bound as driver yet. Note: the
  epic-loop Stop-hook loop is not installed in `.claude/settings.json` yet
  (`doctor` = setup-required); install hooks before starting autonomous
  implementation, or drive Phase 2 manually.
