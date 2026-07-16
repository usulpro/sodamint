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

- Phase status: todo

- [ ] Kind: implementation | Status: todo | Read the live idle/sleep inhibitor list from logind via `login1 ListInhibitors` (Gio D-Bus), filtered per D12, with a `systemd-inhibit --list` parse fallback.
  - Outcome: Sodamint can enumerate every process keeping the machine awake, as structured `(what, who, why, mode, uid, pid)` records.
  - Surface: `sodamint.py` — new helper (e.g. `list_inhibitors()`); `Gio` system-bus call; filter + fallback.
  - Acceptance: Returns the same idle/sleep holders as `systemd-inhibit --list`; returns `[]` (not an exception) when there are none or the bus is unreachable; no new dependency added.
  - Docs: `docs/data-source.md`.
- [ ] Kind: implementation | Status: todo | Drive the icon/status and a dynamic, read-only per-source menu from the inhibitor list; classify each row (agent `◆` / our own `★` / other `●`), group agents first under an `Agents`/`Other` header (D20), no age column (D19); poll on a `GLib.timeout` + on menu popup; rebuild the menu for both backends.
  - Outcome: The tray shows read-only rows (why/who/pid, no age) with agent sources (`who==sodamint-agent`) grouped first and highlighted, and the icon is active iff ≥1 exists.
  - Surface: `sodamint.py` — `_refresh()` derives from the inhibitor list; row classification + grouping per `docs/data-source.md`/`docs/tray-ux.md`; `_build_menu()`/rebuild section; `GLib.timeout_add_seconds`; AppIndicator `set_menu()` + StatusIcon `self._menu`.
  - Acceptance: Starting/stopping an external `systemd-inhibit` makes a row appear/disappear within one poll and flips the icon; `--who=sodamint-agent` inhibitors render as highlighted (`◆`) rows listed before all others under an `Agents` header; our manual lock renders as `★` under `Other`; group headers appear only when non-empty; no age is shown; rows are inert on click; renders on both AppIndicator and StatusIcon.
  - Docs: `docs/tray-ux.md`, `docs/data-source.md`, `docs/agent-integration.md`.
- [ ] Kind: verification | Status: todo | Drive the dashboard with real external + agent inhibitors on both backends and confirm the render/icon/highlight contract.
  - Outcome: Verified that the list mirrors logind, the icon tracks the count, and agent rows are highlighted.
  - Surface: run the app; hold locks via `systemd-inhibit --what=idle:sleep --why=test -- sleep 600` and `systemd-inhibit --what=idle:sleep --who=sodamint-agent --why="epic-loop · test" -- sleep 600`; observe rows, glyphs, icon, header count; compare to `systemd-inhibit --list`.
  - Acceptance: Rows match `--list` (filtered); the agent lock shows the highlighted glyph; icon active with ≥1, inactive at 0; both backends render; cleanup kills the test inhibitors.
  - Docs: `docs/tray-ux.md`, `docs/agent-integration.md`.

### Phase 3: Manual Toggle & Quit

- Phase status: todo

- [ ] Kind: implementation | Status: todo | Reconcile the manual toggle with the new model: it holds our own inhibitor (unchanged `start`/`stop`/`is_on`), shows as its own `★` row, and the Quit item's label is dynamic — `Quit` when off, `Disable and quit` when on (D21), updated in `_refresh()`; no confirmation dialog. No behavior change to the existing lock/unlock path.
  - Outcome: The classic one-click keep-awake still works exactly as today and is consistent with the dashboard; quitting never silently sleeps a machine held by others, and the Quit label states whether it will drop our lock.
  - Surface: `sodamint.py` — `_on_toggle_item`/`start`/`stop`/`is_on`/`quit`; Quit `Gtk.MenuItem` label set from `is_on()` in `_refresh()`; identify our row by `self.proc.pid`; `child_watch`/`_on_child_exit` preserved.
  - Acceptance: Toggle on → machine held + our `★` row + active icon + Quit label reads `Disable and quit`; toggle off → lock released, row gone, Quit label reads `Quit`; external death of our subprocess still resets state and the label (existing `_on_child_exit` → `_refresh()`); quitting drops only our lock and leaves external rows (verified via `--list` after quit).
  - Docs: `docs/tray-ux.md`, `docs/data-source.md`.
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

## Retired Roadmap (pre-2026-07-17 reset — not being built)

Kept for history. These phases assumed the lease/refcount/watchdog architecture
that the reset discarded because logind already provides it. Do **not** pick up
tasks from here.

- **Retired Phase 2 — Lease Core & CLI**: lease store (`$XDG_RUNTIME_DIR/sodamint/leases/*.json`), CLI `acquire`/`release`/`heartbeat`/`list`/`status`. Superseded: `systemd-inhibit` is the acquire/release CLI; logind is the store.
- **Retired Phase 3 — Reference-counted inhibitor + FileMonitor**: single app-owned inhibitor gated on `lease_count > 0`. Superseded: logind reference-counts each holder's own inhibitor.
- **Retired Phase 4 — Watchdog & Liveness**: PID/start-time/watch-file/heartbeat pruning. Superseded: kernel closes the fd on holder death; "alive but hung" is handled by manual drop (user's choice).
- **Retired Phase 5 — `run -- <cmd>` wrapper**: scope-guard acquire/run/release. Superseded: that is literally `systemd-inhibit -- <cmd>`.
