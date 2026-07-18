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

## 2026-07-18 - Phase 3 Task 1: dynamic Quit label + child-reap fix (implementation, closed)

- `sodamint.py`: (A) `_build_menu` sets the Quit item label to
  `"Disable and quit" if on else "Quit"` (D21) — delivered via the existing
  `on`-keyed menu rebuild, no dialog, `quit()` unchanged. (B) fixed the
  pre-existing `waitid: No child processes` warning: `start()` stores the
  child-watch source id in `self._child_watch`; `stop()` `GLib.source_remove()`s
  it before `terminate()`/`wait()`; `_on_child_exit` clears it (one-shot).
  Observable lock/unlock semantics unchanged.
- Verified (AppIndicator): label off→`Quit`, on→`Disable and quit`, off→`Quit`;
  `★` row + checkbox track state; no `waitid` warning on stderr through a real
  start/settle/stop under a GLib tick; external SIGTERM of our subprocess still
  resets `self.proc`/UI via the preserved `_on_child_exit`; quit isolation —
  `stop()` releases only our lock, an external `p3-ext-survive` lock survives in
  `list_inhibitors()`. Techlead independently re-verified label + warning + clean
  start/stop.
- Risk-register: the `waitid` double-reap risk is now `resolved`.
- Process-hygiene note: engineer's first (crashed) attempt leaked one orphaned
  `systemd-inhibit … sleep infinity`; found and killed during cleanup. Lesson
  carried into the task-2 brief: wrap `start()` in try/finally `stop()` and allow
  a settle before asserting the async `★` row.
- Not committed: `.claude/settings.json` (unrelated hook-install infra).

## 2026-07-18 - Phase 3 Task 2: toggle regression + quit isolation (verification, closed) — PHASE 3 COMPLETE

- In-process verification with real GLib/Gtk loops; every start() wrapped in
  try/finally stop(); _refresh() called post-settle to mirror a poll after
  logind's async registration.
- All 6 criteria PASS on both AppIndicator and StatusIcon backends:
  1. Toggle parity: 3 on/off cycles per backend, our lock pid appears/disappears
     in list_inhibitors() each cycle, no residue.
  2. UI tracking: on → is_on/checkbox/★(at self.proc.pid)/active-icon/Quit
     "Disable and quit"; off → the inverse.
  3. External death: os.kill(SIGTERM) → UI resets via _on_child_exit, no warning.
  4. Quit isolation via the REAL quit() (stop()+Gtk.main_quit() inside Gtk.main()):
     our lock dropped, external `sodamint-agent · p3 quit-iso` lock survived.
  5. Both backends exercised (criterion 4 shown on AppIndicator).
  6. No `waitid` warning across all cycles.
- No product code changed; no defects. Test inhibitors cleaned up; no stray
  `sleep infinity`; no app process left running.
- Design note (not a defect): after a manual toggle-on the ★ row lands on the
  next poll (≤POLL_SECONDS) because logind registration is async; icon/checkbox/
  Quit-label update instantly from is_on().
- **Phase 3 (Manual Toggle & Quit) is complete.**

## 2026-07-18 - Phase 4 Task 1: repo docs aligned to the dashboard model (implementation, closed)

- `CLAUDE.md`: reworked "What this is" + "How it works" (two non-obvious things:
  our own lock is a subprocess AND the tray reflects logind) and the architecture
  notes — `self.proc` is source of truth only for our own lock (D17); icon active
  iff any source; `_refresh()` repaints from `list_inhibitors()`; grouped
  `◆`/`★`/`●` read-only rows; dynamic Quit label; rebuild-not-mutate with the
  change-signature guard; the checkbox guard is now set-before-connect (the old
  `handler_block_by_func` is gone); `stop()` removes the child-watch source; agent
  contract pointer. Dropped the stale "~200 lines".
- New repo-root `AGENTS.md`: agent keep-awake contract surfaced from
  `docs/agent-integration.md` — wrap one-liner, field table
  (what/who/why/mode), explicit-hold variant + leak caveat, read-only/auto-release
  notes, `AGENT_WHO` lockstep pointer.
- `install.sh`: confirmed correct, no change (same single file, icons,
  `sodamint.desktop`, and dep probe).
- Verified: py_compile sanity OK (no code change); each corrected CLAUDE.md claim
  cross-checked against `sodamint.py`; marker string matches `AGENT_WHO`; the
  documented one-liner run verbatim → `list_inhibitors()` shows it and
  `_classify(..., None) == 'agent'` (glyph `◆`). Test lock cleaned up.
- Not committed: `.claude/settings.json` (unrelated infra).

## 2026-07-18 - Phase 4 Task 2: whole-feature E2E (verification, closed) — PHASE 4 COMPLETE

- In-process AppIndicator run with a real Gtk.main() loop; two agent inhibitors
  spawned via subprocess.Popen using the AGENTS.md one-liner form (exact pids);
  POLL_SECONDS=4.
- All 4 steps PASS:
  1. 2 agents + manual ON → `Awake — 10 sources`, two `◆` rows grouped first, one
     `★` (this) row; both agents confirmed in logind.
  2. Toggle OFF → `★` gone + our lock released; both `◆` remain; still active.
  3. External SIGTERM of agent A → its `◆` disappears within a poll (logind
     auto-cleanup, no code of ours); agent B remains.
  4. Real quit() (Gtk.main_quit) → agent B still held in logind, our lock gone —
     quitting does not sleep a machine an agent is still holding.
- No `waitid` warning; no product code changed; all test locks cleaned up.
- Process-hygiene lesson: two pre-run harness attempts used shell
  `pgrep -f "p4e2e"` which self-matched the running shell and SIGTERM'd the
  script (exit 144), briefly orphaning agent locks (cleaned by extracting exact
  pids via list_inhibitors()). Rewrote to spawn/clean agents entirely in Python
  with a finally. Never `pgrep -f <token>` when the driver command contains it.
- **Phase 4 (Docs & End-to-End) is complete.** The reshaped desired outcome is
  proven end-to-end.

## 2026-07-18 - Phase 5 Task 1: .deb build recipe (implementation, closed)

- New `packaging/build-deb.sh`: stages the install.sh file map system-wide
  (`/usr/share/sodamint/sodamint.py`, `/usr/bin/sodamint` launcher, icons →
  hicolor/scalable/status, `sodamint.desktop` → applications), writes
  `DEBIAN/control` + `postinst`/`postrm` (icon/desktop cache refresh), and packs
  with `dpkg-deb --build --root-owner-group`. `VERSION=0.1.0`; optional out dir
  (default `dist/`). Uses only dpkg-deb (debuild/fpm/lintian absent here).
- New `docs/packaging.md`: build steps, file-layout table, Depends↔check_deps
  lockstep, version bump point, artifact location, inspection commands.
- `.gitignore`: added `dist/` + `*.deb` (built package is an artifact, not
  source — only the recipe + docs are committed).
- Verified (techlead re-ran): `Architecture: all`; `Depends: python3-gi,
  gir1.2-gtk-3.0, gir1.2-ayatanaappindicator3-0.1, systemd` (exact install.sh
  set); file map + modes correct; launcher body
  `exec python3 /usr/share/sodamint/sodamint.py "$@"`; package root 0755;
  py_compile OK; `.deb` confirmed gitignored. `sodamint.py` unchanged.
- Not committed: the built `.deb` (dist/) and `.claude/settings.json`.
- Constraint for task 2: clean-env `apt install` needs a container/VM or a
  deps-purge (this host already has the runtime deps installed).

## 2026-07-18 - Phase 5 Task 2: clean-env .deb install (verification, closed)

- Fresh `ubuntu:24.04` Docker container (rootless docker), full
  install→verify→remove flow. All 4 packaging criteria PASS:
  1. `apt install ./sodamint_0.1.0_all.deb` auto-resolved + installed the four
     deps (python3-gi, gir1.2-gtk-3.0, gir1.2-ayatanaappindicator3-0.1, systemd);
     no `universe` enable needed on stock 24.04.
  2. `dpkg -L` shows the correct file map; launcher executable.
  3. Installed `.py` `py_compile`s; `import gi; Gtk 3.0; Gio/GLib/Gtk` → imports ok.
  4. `apt remove` removes all files incl. `/usr/share/sodamint`; `purge` leaves
     no dpkg record.
- Runtime keep-awake not container-testable (no live logind/system bus) —
  already host-verified in Phases 2–4.
- Verification-method note: a first run showed `/usr/share/sodamint` STRAY after
  remove; root cause was Step-3 `py_compile` writing `__pycache__` into the
  install dir (unowned → dir non-empty → dpkg can't rmdir). Re-run with
  `PYTHONPYCACHEPREFIX=/tmp/pycache` confirmed clean removal. NOT a packaging
  defect; recipe unchanged. Lesson: don't py_compile a package's installed file
  in place during a removal test.
- No files changed (verification only); rebuilt `.deb` is gitignored.

## 2026-07-18 - Phase 5 Task 3: README + GitHub Release path (implementation, closed)

- New repo-root `README.md`: user-facing — what-it-is, install via release `.deb`
  (`sudo apt install ./sodamint_0.1.0_all.deb`, apt-resolved deps), run-from-source
  / `install.sh` alternative, agent keep-awake pointer to `AGENTS.md`, and a
  build/architecture pointer to `CLAUDE.md` + `docs/packaging.md`.
- `docs/packaging.md`: added "Publishing a GitHub Release" — the user-gated
  `build → git tag v0.1.0 → git push → gh release create v0.1.0
  dist/sodamint_0.1.0_all.deb …` procedure (explicitly maintainer-run, needs a
  remote + `gh auth login`) plus a pasteable v0.1.0 release-notes draft.
- Version/tag `v0.1.0` (lockstep with `VERSION=` in build-deb.sh and the artifact
  name). Verified: README + gh command reference the exact artifact filename;
  `.deb` rebuilt; nothing published (no tags, no remote — publish is user-gated
  and impossible here by design); py_compile OK. `sodamint.py` unchanged.
- Not committed: built `.deb` (gitignored) and `.claude/settings.json`.
