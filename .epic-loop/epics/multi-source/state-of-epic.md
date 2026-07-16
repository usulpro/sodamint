# State Of Epic

Epic: Inhibitor Dashboard For Sodamint
Slug: `multi-source`
Created: 2026-07-14T10:21:11+00:00
Mode: shaping
Active phase: Phase 1 - Shape The Epic (done, reshaped) → ready for Phase 2
Active task: TBD (next: Phase 2 — read & render inhibitors)

## Current State

- **Strategic reset applied 2026-07-17.** A prior design session (transcript
  `e7c91d0e` in the `sodamint/Sodamint` folder) found the original
  lease/refcount/watchdog service ~80% redundant with `systemd-inhibit`/logind
  (including crash cleanup). Per user direction, the epic is now a thin **tray
  UI over logind's inhibitor list**: show every idle/sleep source (who/why/pid)
  and let the user manually drop one. No lease store, CLI, in-app refcount, or
  watchdog.
- Decisions reshaped: **D10–D18** define the new architecture and **supersede
  D1–D8**; **D9** (do not port to macOS) stands and is more central now.
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
- `tracker.md` reshaped to a 4-phase roadmap (Shape → Read&Render(+highlight) →
  Manual Toggle&Quit → Docs&E2E); the old lease/CLI/watchdog/wrapper phases are
  retired at the bottom.

## Blockers

- None. Three open questions remain in `decision-log.md` (age column source;
  agent-highlight style; quit confirm), all with leaning answers — decide during
  Phase 2/3. The old external-drop questions (SIGTERM-vs-SIGKILL, confirm scope)
  are resolved/moot by D14.

## Next Action

- Await user confirmation on the reshaped scope, then move to implementation
  starting at Phase 2 (read & render inhibitors from logind).
- Implementation is NOT started; no session is bound as driver yet. Note: the
  epic-loop Stop-hook loop is not installed in `.claude/settings.json` yet
  (`doctor` = setup-required); install hooks before starting autonomous
  implementation, or drive Phase 2 manually.
