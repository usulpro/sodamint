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
  - Docs: `docs/problem-framing.md`, `docs/tray-ux.md`, `docs/data-source.md`, `docs/macos-feasibility.md`.
- [x] Kind: architecture-reset | Status: done | Reshape from a lease/refcount/watchdog service to a thin tray UI over logind's inhibitor list.
  - Outcome: The epic no longer rebuilds what `systemd-inhibit`/logind already does; scope is visibility + manual drop only.
  - Surface: `decision-log.md` (D10–D17 supersede D1–D8), `docs/problem-framing.md`, `docs/tray-ux.md`, new `docs/data-source.md`; `docs/cli-reference.md` + `docs/watch-mode.md` marked superseded.
  - Acceptance: No active artifact prescribes a lease store, CLI, in-app refcount, or watchdog; the reset rationale is recorded with a pointer to the prior-session analysis.
  - Docs: `decision-log.md`.

### Phase 2: Read & Render Inhibitors

- Phase status: todo

- [ ] Kind: implementation | Status: todo | Read the live idle/sleep inhibitor list from logind via `login1 ListInhibitors` (Gio D-Bus), filtered per D12, with a `systemd-inhibit --list` parse fallback.
  - Outcome: Sodamint can enumerate every process keeping the machine awake, as structured `(what, who, why, mode, uid, pid)` records.
  - Surface: `sodamint.py` — new helper (e.g. `list_inhibitors()`); `Gio` system-bus call; filter + fallback.
  - Acceptance: Returns the same idle/sleep holders as `systemd-inhibit --list`; returns `[]` (not an exception) when there are none or the bus is unreachable; no new dependency added.
  - Docs: `docs/data-source.md`.
- [ ] Kind: implementation | Status: todo | Drive the icon/status and a dynamic per-source menu from the inhibitor list; poll on a `GLib.timeout` + on menu popup; rebuild the menu for both backends.
  - Outcome: The tray shows one row per idle/sleep inhibitor (why/who/pid, age if cheap) and the icon is active iff ≥1 exists.
  - Surface: `sodamint.py` — `_refresh()` derives from the inhibitor list; `_build_menu()`/rebuild section; `GLib.timeout_add_seconds`; AppIndicator `set_menu()` + StatusIcon `self._menu`.
  - Acceptance: Starting/stopping an external `systemd-inhibit` makes a row appear/disappear within one poll and flips the icon; manual toggle appears as its own row; renders on both AppIndicator and StatusIcon.
  - Docs: `docs/tray-ux.md`, `docs/data-source.md`.
- [ ] Kind: verification | Status: todo | Drive the dashboard with real external inhibitors on both backends and confirm the render/icon contract.
  - Outcome: Verified that the list mirrors logind and the icon tracks the count.
  - Surface: run the app; hold locks via `systemd-inhibit --what=idle:sleep --why=test -- sleep 600` (one or more); observe rows, icon, header count; compare to `systemd-inhibit --list`.
  - Acceptance: Rows match `--list` (filtered); icon active with ≥1, inactive at 0; both backends render; cleanup kills the test inhibitors.
  - Docs: `docs/tray-ux.md`.

### Phase 3: Manual Drop & Manual Toggle

- Phase status: todo

- [ ] Kind: implementation | Status: todo | Per-source "Release this source": terminate our own subprocess for our lock, else `SIGTERM` the holder pid with a confirm dialog; handle `EPERM`/`ESRCH` gracefully and re-poll.
  - Outcome: The user can drop any idle/sleep source from the tray, including a hung agent, without a terminal.
  - Surface: `sodamint.py` — submenu `Release` handler; branch on `pid == self.proc.pid`; `os.kill`; confirm + error dialogs; refresh after.
  - Acceptance: Dropping an external test inhibitor removes its row within one poll; a non-permitted pid shows an error instead of crashing; our own lock is released cleanly without a kill.
  - Docs: `docs/tray-ux.md`, `docs/data-source.md`.
- [ ] Kind: implementation | Status: todo | Reconcile the manual toggle with the new model: it holds our own inhibitor (unchanged `start`/`stop`), shows as its own row, and quit drops only our lock (light confirm only when the toggle is on).
  - Outcome: The classic one-click keep-awake still works and is consistent with the dashboard; quitting never silently sleeps a machine held by others.
  - Surface: `sodamint.py` — `_on_toggle_item`/`start`/`stop`/`quit`; identify our row by `self.proc.pid`.
  - Acceptance: Toggle on → our row + active icon; toggle off → row gone; quit with toggle on drops only our lock and leaves external rows (verified via `--list` after quit); quit with toggle off exits immediately.
  - Docs: `docs/tray-ux.md`.
- [ ] Kind: verification | Status: todo | Exercise drop + toggle + quit against the full behavior set on both backends.
  - Outcome: Verified control surface (drop own/external, confirm, permission failure, quit isolation).
  - Surface: run the app; external `systemd-inhibit` holders + manual toggle; drop each; attempt a non-permitted drop; quit and re-check `systemd-inhibit --list`.
  - Acceptance: Every case behaves per `tray-ux.md`/`data-source.md`; no crash on `EPERM`/`ESRCH`; external sources survive our quit.
  - Docs: `docs/tray-ux.md`, `docs/data-source.md`.

### Phase 4: Docs & End-to-End

- Phase status: todo

- [ ] Kind: implementation | Status: todo | Update `CLAUDE.md` to the reshaped model (dashboard over logind; `self.proc` is source of truth only for our own lock — D17) and document the recommended agent integration (`systemd-inhibit --why="…" -- <cmd>`); refresh `install.sh`/README if needed.
  - Outcome: Repo docs match the shipped behavior; agents have a copy-paste keep-awake pattern that shows up in the dashboard and self-releases.
  - Surface: `CLAUDE.md`, optionally README/`install.sh`.
  - Acceptance: `CLAUDE.md` no longer claims `self.proc` is the *only* source of truth and describes the dashboard; the documented agent wrapper appears as a row when run.
  - Docs: `docs/problem-framing.md`, `docs/data-source.md`.
- [ ] Kind: verification | Status: todo | Whole-feature run mimicking the real workload: two parallel `systemd-inhibit -- <cmd>` "agents" plus the manual toggle; drop one; kill one; quit.
  - Outcome: End-to-end proof against the reshaped desired outcome.
  - Surface: live app + two `systemd-inhibit --why=… -- sleep 600` + manual toggle + `systemd-inhibit --list`.
  - Acceptance: All three show as rows; icon active; manual "Release" drops one; externally killing an agent removes its row within a poll (logind auto-cleanup); quitting leaves the surviving external agent holding the machine awake.
  - Docs: `docs/problem-framing.md`, `docs/data-source.md`.

## Retired Roadmap (pre-2026-07-17 reset — not being built)

Kept for history. These phases assumed the lease/refcount/watchdog architecture
that the reset discarded because logind already provides it. Do **not** pick up
tasks from here.

- **Retired Phase 2 — Lease Core & CLI**: lease store (`$XDG_RUNTIME_DIR/sodamint/leases/*.json`), CLI `acquire`/`release`/`heartbeat`/`list`/`status`. Superseded: `systemd-inhibit` is the acquire/release CLI; logind is the store.
- **Retired Phase 3 — Reference-counted inhibitor + FileMonitor**: single app-owned inhibitor gated on `lease_count > 0`. Superseded: logind reference-counts each holder's own inhibitor.
- **Retired Phase 4 — Watchdog & Liveness**: PID/start-time/watch-file/heartbeat pruning. Superseded: kernel closes the fd on holder death; "alive but hung" is handled by manual drop (user's choice).
- **Retired Phase 5 — `run -- <cmd>` wrapper**: scope-guard acquire/run/release. Superseded: that is literally `systemd-inhibit -- <cmd>`.
