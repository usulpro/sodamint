# Tracker

Epic: Inhibitor Dashboard For Sodamint (slug `multi-source`)

> **Reshaped 2026-07-17 (strategic reset).** The old 5-phase roadmap (lease
> core + CLI, reference-counted inhibitor, watchdog, wrapper) is **retired** —
> logind already provides all of it. See the reset note in `decision-log.md`.
> Retired phases are kept at the bottom for history.

## Task Statuses

- todo
- doing
- need-review
- blocked
- partially-satisfied
- deferred
- reset-required
- done

## Task Kinds

- implementation
- verification
- review
- follow-up
- architecture-reset
- documentation-only

## Active Roadmap

### Phase 1: Shape The Epic

- Phase status: done

- [x] Kind: documentation-only | Status: done | Capture problem framing, scope, decisions, risks, and the design docs.
  - Outcome: The epic has enough structure to decompose implementation.
  - Surface: `docs/`, `decision-log.md`, `risk-register.md`, `state-of-epic.md`.
  - Acceptance: A future session understands why this epic exists and what to build next.
  - Docs: `docs/problem-framing.md`, `docs/tray-ux.md`, `docs/data-source.md`, `docs/agent-integration.md`, `docs/macos-feasibility.md`.
- [x] Kind: architecture-reset | Status: done | Reshape from a lease/refcount/watchdog service to a thin tray UI over logind's inhibitor list.
  - Outcome: The epic no longer rebuilds what `systemd-inhibit`/logind already does; scope is visibility + manual drop only.
  - Surface: `decision-log.md` (D10–D17 supersede D1–D8), `docs/problem-framing.md`, `docs/tray-ux.md`, new `docs/data-source.md`; `docs/cli-reference.md` + `docs/watch-mode.md` marked superseded.
  - Acceptance: No active artifact prescribes a lease store, CLI, in-app refcount, or watchdog; the reset rationale is recorded with a pointer to the prior-session analysis.
  - Docs: `decision-log.md`.

### Phase 2: Read & Render Inhibitors

- Phase status: done (2026-07-18 — read path + dashboard render + end-to-end verification on both backends)

- [x] Kind: implementation | Status: done | Read the live idle/sleep inhibitor list from logind via `login1 ListInhibitors` (Gio D-Bus), filtered per D12, with a `systemd-inhibit --list` parse fallback.
  - Outcome: Sodamint can enumerate every process keeping the machine awake, as structured `(what, who, why, mode, uid, pid)` records.
  - Surface: `sodamint.py` — new helper (e.g. `list_inhibitors()`); `Gio` system-bus call; filter + fallback.
  - Acceptance: Returns the same idle/sleep holders as `systemd-inhibit --list`; returns `[]` (not an exception) when there are none or the bus is unreachable; no new dependency added.
  - Docs: `docs/data-source.md`.
  - Closed 2026-07-18: added `Inhibitor` namedtuple + `list_inhibitors()` (`_list_inhibitors_dbus` primary, `_list_inhibitors_fallback` column-offset parse, `_keeps_awake` D12 filter). Verified against live logind: 10 raw → filtered idle/sleep set, test lock appears/disappears, D-Bus/fallback parity, `[]` on both-sources-fail, no new dep. Commit-owned.
- [x] Kind: implementation | Status: done | Drive the icon/status and a dynamic, read-only per-source menu from the inhibitor list; classify each row (agent `◆` / our own `★` / other `●`), group agents first under an `Agents`/`Other` header (D20), no age column (D19); poll on a `GLib.timeout` + on menu popup; rebuild the menu for both backends.
  - Outcome: The tray shows read-only rows (why/who/pid, no age) with agent sources (`who==sodamint-agent`) grouped first and highlighted, and the icon is active iff ≥1 exists.
  - Surface: `sodamint.py` — `_refresh()` derives from the inhibitor list; row classification + grouping per `docs/data-source.md`/`docs/tray-ux.md`; `_build_menu()`/rebuild section; `GLib.timeout_add_seconds`; AppIndicator `set_menu()` + StatusIcon `self._menu`.
  - Acceptance: Starting/stopping an external `systemd-inhibit` makes a row appear/disappear within one poll and flips the icon; `--who=sodamint-agent` inhibitors render as highlighted (`◆`) rows listed before all others under an `Agents` header; our manual lock renders as `★` under `Other`; group headers appear only when non-empty; no age is shown; rows are inert on click; renders on both AppIndicator and StatusIcon.
  - Docs: `docs/tray-ux.md`, `docs/data-source.md`, `docs/agent-integration.md`.
  - Closed 2026-07-18: added pure helpers (`_classify`/`_row_label`/`_group_inhibitors`/`_status_text`, `GLYPH`, `AGENT_WHO`); `_refresh()` now repaints icon (active iff ≥1, D13), status header, and a rebuilt grouped read-only menu with a change-signature guard; `POLL_SECONDS=4` timer + StatusIcon popup refresh; checkbox state set before handler connect (feedback guard survives rebuild). Verified: unit helpers, live AppIndicator render (agent `◆` grouped first + `●` others), StatusIcon construct + inert rows + Idle state, real own-lock `★` with pid match, no double-trigger. Lifecycle (`start`/`stop`/`is_on`/`toggle`/`_on_child_exit`) byte-for-byte unchanged. Full both-backends visual + icon-flip-within-poll check is task 3.
- [x] Kind: verification | Status: done | Drive the dashboard with real external + agent inhibitors on both backends and confirm the render/icon/highlight contract.
  - Outcome: Verified that the list mirrors logind, the icon tracks the count, and agent rows are highlighted.
  - Surface: run the app; hold locks via `systemd-inhibit --what=idle:sleep --why=test -- sleep 600` and `systemd-inhibit --what=idle:sleep --who=sodamint-agent --why="epic-loop · test" -- sleep 600`; observe rows, glyphs, icon, header count; compare to `systemd-inhibit --list`.
  - Acceptance: Rows match `--list` (filtered); the agent lock shows the highlighted glyph; icon active with ≥1, inactive at 0; both backends render; cleanup kills the test inhibitors.
  - Docs: `docs/tray-ux.md`, `docs/agent-integration.md`.
  - Closed 2026-07-18: ran in-process with a real `GLib.MainLoop` so the `POLL_SECONDS=4` timer fired. All 6 criteria PASS on **both** backends — poll auto-picked up an external lock (no manual `_refresh`) and dropped it within one interval; agent `◆` rendered first under `Agents`; menu source-row pids matched `list_inhibitors()` one-to-one; icon-at-zero → `Idle`+`sodamint-inactive` (simulated empty, since the live host always holds ≥7); rows inert. No defects; test inhibitors cleaned up. Live active→inactive icon flip not observable on real data (host never reaches 0 sources) — covered by the simulated-empty path.

### Phase 3: Manual Toggle & Quit

- Phase status: todo

- [x] Kind: implementation | Status: done | Reconcile the manual toggle with the new model: it holds our own inhibitor (unchanged `start`/`stop`/`is_on`), shows as its own `★` row, and the Quit item's label is dynamic — `Quit` when off, `Disable and quit` when on (D21), updated in `_refresh()`; no confirmation dialog. No behavior change to the existing lock/unlock path.
  - Outcome: The classic one-click keep-awake still works exactly as today and is consistent with the dashboard; quitting never silently sleeps a machine held by others, and the Quit label states whether it will drop our lock.
  - Surface: `sodamint.py` — `_on_toggle_item`/`start`/`stop`/`is_on`/`quit`; Quit `Gtk.MenuItem` label set from `is_on()` in `_refresh()`; identify our row by `self.proc.pid`; `child_watch`/`_on_child_exit` preserved.
  - Acceptance: Toggle on → machine held + our `★` row + active icon + Quit label reads `Disable and quit`; toggle off → lock released, row gone, Quit label reads `Quit`; external death of our subprocess still resets state and the label (existing `_on_child_exit` → `_refresh()`); quitting drops only our lock and leaves external rows (verified via `--list` after quit).
  - Docs: `docs/tray-ux.md`, `docs/data-source.md`.
  - Closed 2026-07-18: `_build_menu` computes the Quit label from `on` (no dialog; delivered via the existing `on`-keyed rebuild). Also fixed the pre-existing `waitid: No child processes` warning — `start` stores the child-watch source id, `stop` `GLib.source_remove()`s it before reaping, `_on_child_exit` clears it; lock/unlock semantics unchanged. Verified: label off/on/off; no warning on stderr; external SIGTERM still resets UI via `_on_child_exit`; quit isolation (`stop()` drops only our lock, external `p3-ext-survive` survives). `★`/checkbox tracking still holds (Phase 2). Full both-backends regression is task 2.
- [ ] Kind: verification | Status: todo | Confirm the manual toggle is a strict regression-safe superset of today's behavior, plus quit isolation, on both backends.
  - Outcome: Verified that existing manual keep-awake did not regress and quit never drops a lock we do not own.
  - Surface: run the app; toggle on/off repeatedly and confirm the inhibitor via `systemd-inhibit --list`; kill our subprocess externally and confirm the UI recovers; with an external agent lock present, quit and re-check `--list`.
  - Acceptance: Lock appears/disappears with the toggle exactly as before the epic; external subprocess death resets the checkbox/icon; after quit-with-external-source-present the external inhibitor is still listed.
  - Docs: `docs/tray-ux.md`.

### Phase 4: Docs & End-to-End

- Phase status: todo

- [ ] Kind: implementation | Status: todo | Update `CLAUDE.md` to the reshaped model (dashboard over logind; `self.proc` is source of truth only for our own lock — D17) and point agents at the integration contract; surface the contract in repo-level docs (e.g. an `AGENTS.md` or README section) copied from `docs/agent-integration.md`; refresh `install.sh` if needed.
  - Outcome: Repo docs match the shipped behavior; agents have a copy-paste, highlighted keep-awake pattern in project documentation.
  - Surface: `CLAUDE.md`, repo agent doc (new `AGENTS.md` or README section), optionally `install.sh`.
  - Acceptance: `CLAUDE.md` no longer claims `self.proc` is the *only* source of truth and describes the dashboard; the `--who=sodamint-agent` contract is documented at repo level and, when followed, produces a highlighted row.
  - Docs: `docs/problem-framing.md`, `docs/data-source.md`, `docs/agent-integration.md`.
- [ ] Kind: verification | Status: todo | Whole-feature run mimicking the real workload: two parallel agent inhibitors (`--who=sodamint-agent`) plus the manual toggle; toggle off; externally kill one agent; quit.
  - Outcome: End-to-end proof against the reshaped desired outcome.
  - Surface: live app + two `systemd-inhibit --what=idle:sleep --who=sodamint-agent --why=… -- sleep 600` + manual toggle + `systemd-inhibit --list`.
  - Acceptance: All three show as rows (two highlighted `◆`, one `★`); icon active; toggling the manual lock off drops only our row; externally killing an agent removes its row within a poll (logind auto-cleanup, no code of ours); quitting leaves the surviving external agents holding the machine awake.
  - Docs: `docs/problem-framing.md`, `docs/agent-integration.md`.

### Phase 5: Packaging & Distribution

- Phase status: todo

- [ ] Kind: implementation | Status: todo | Build an installable `.deb` (`Architecture: all`) with apt-resolved dependencies, reusing the file layout and dep list from `install.sh`.
  - Outcome: One `.deb` that installs Sodamint system-wide and pulls its GTK/AppIndicator/systemd deps via apt.
  - Surface: new `packaging/` (a `debian/` control dir + build script, or an `fpm` recipe): `Depends: python3-gi, gir1.2-gtk-3.0, gir1.2-ayatanaappindicator3-0.1, systemd`; file map (`sodamint.py`→`/usr/share/sodamint` + `/usr/bin/sodamint` launcher, icons→`hicolor/scalable/status`, `sodamint.desktop`→`/usr/share/applications`); `postinst` running `gtk-update-icon-cache`/`update-desktop-database` (mirrors `install.sh`).
  - Acceptance: `dpkg-deb`/`debuild` produces `sodamint_<v>_all.deb`; `apt-cache`/`dpkg -I` shows the correct `Depends`; the dep list matches `install.sh check_deps`.
  - Docs: `docs/packaging.md` (new), `docs/problem-framing.md`.
- [ ] Kind: verification | Status: todo | Install the built `.deb` end-to-end in a clean environment and confirm the packaged app runs and keeps-awake.
  - Outcome: Proven that the package installs, resolves deps, launches, and holds/releases a lock with only its declared dependencies.
  - Surface: a clean container/VM (or deps-purged check); `sudo apt install ./sodamint_<v>_all.deb`; launch `sodamint`; observe tray + `systemd-inhibit --list`; `sudo apt remove sodamint`.
  - Acceptance: Fresh install auto-resolves `python3-gi`/`gir1.2-*`; tray icon appears; manual toggle holds then releases an inhibitor (via `--list`); `apt remove` leaves no stray files (icons/desktop deregistered).
  - Docs: `docs/packaging.md`.
- [ ] Kind: implementation | Status: todo | Prepare a GitHub Release for the `.deb` and document the user install path; the actual publish is a user-gated one-command step.
  - Outcome: A tagged release carries the `.deb`, and the README tells users how to install it.
  - Surface: repo `README` install section (`sudo apt install ./sodamint_<v>_all.deb`); a documented `gh release create <tag> sodamint_<v>_all.deb` procedure in `docs/packaging.md`; version/tag chosen.
  - Acceptance: The `.deb` artifact + release notes + README snippet are ready; publishing is one documented command run by the user (outward-facing action, not auto-run by the agent).
  - Docs: `docs/packaging.md`, repo `README`.
- [ ] Kind: documentation-only | Status: todo | Write a Launchpad PPA publishing how-to for later (no PPA created now).
  - Outcome: A future session can put the same package on a PPA without re-researching.
  - Surface: new `docs/publishing-ppa.md`.
  - Acceptance: The doc covers Launchpad account + GPG key, turning the `packaging/` deb into a source package (`debian/` + `changelog`, `debuild -S`), `dput` upload, and the end-user `add-apt-repository ppa:<owner>/sodamint && apt install sodamint` flow; enough to follow step-by-step.
  - Docs: `docs/publishing-ppa.md`, `docs/packaging.md`.
- [ ] Kind: documentation-only | Status: todo | Write a Flatpak feasibility & requirements doc — decide-later, do NOT adapt the app now (D22).
  - Outcome: A clear record of what Flatpak would take, so the choice is informed and the required changes are known, without touching the code yet.
  - Surface: new `docs/flatpak-feasibility.md` (mirrors the `docs/macos-feasibility.md` pattern).
  - Acceptance: The doc lists the sandbox blockers (no `systemd-inhibit` binary → holding must move to the login1 `Inhibit()` D-Bus fd; SNI/AppIndicator tray), the manifest permissions (`--system-talk-name=org.freedesktop.login1`, StatusNotifier), the Flathub submission flow, and states explicitly that the app is **not** adapted now — Flatpak is gated on the `Inhibit()`-fd change; cross-links `docs/data-source.md` (D11) and D22.
  - Docs: `docs/flatpak-feasibility.md`, `docs/data-source.md`.

## Retired Roadmap (pre-2026-07-17 reset — not being built)

Kept for history. These phases assumed the lease/refcount/watchdog architecture
that the reset discarded because logind already provides it. Do **not** pick up
tasks from here.

- **Retired Phase 2 — Lease Core & CLI**: lease store (`$XDG_RUNTIME_DIR/sodamint/leases/*.json`), CLI `acquire`/`release`/`heartbeat`/`list`/`status`. Superseded: `systemd-inhibit` is the acquire/release CLI; logind is the store.
- **Retired Phase 3 — Reference-counted inhibitor + FileMonitor**: single app-owned inhibitor gated on `lease_count > 0`. Superseded: logind reference-counts each holder's own inhibitor.
- **Retired Phase 4 — Watchdog & Liveness**: PID/start-time/watch-file/heartbeat pruning. Superseded: kernel closes the fd on holder death; "alive but hung" is handled by manual drop (user's choice).
- **Retired Phase 5 — `run -- <cmd>` wrapper**: scope-guard acquire/run/release. Superseded: that is literally `systemd-inhibit -- <cmd>`.
