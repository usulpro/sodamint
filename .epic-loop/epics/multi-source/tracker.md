# Tracker

Epic: Multi-source Keep-awake For Sodamint

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

- [x] Kind: documentation-only | Status: done | Capture problem framing, scope, decisions, risks, and the four requested design docs.
  - Outcome: The epic has enough structure to decompose implementation.
  - Surface: `docs/`, `decision-log.md`, `risk-register.md`, `state-of-epic.md`.
  - Acceptance: A future session understands why this epic exists and what to build next.
  - Docs: `docs/problem-framing.md`, `docs/cli-reference.md`, `docs/tray-ux.md`, `docs/watch-mode.md`, `docs/macos-feasibility.md`.

### Phase 2: Lease Core & CLI

- Phase status: todo

- [ ] Kind: implementation | Status: todo | Lease store module: atomic write/read/list/remove of `$XDG_RUNTIME_DIR/sodamint/leases/*.json`.
  - Outcome: A durable, race-safe on-disk representation of leases.
  - Surface: `sodamint.py` (new lease-store helpers), lease JSON schema per `docs/watch-mode.md`.
  - Acceptance: Concurrent writers never produce a partial/corrupt file; unparseable files are skipped, not fatal.
  - Docs: `docs/watch-mode.md`.
- [ ] Kind: implementation | Status: todo | CLI dispatch on argv: `acquire`, `release`, `heartbeat`, `list`, `status` act as filesystem clients without starting the GUI.
  - Outcome: Agents can manage leases from the shell; daemon not required.
  - Surface: `sodamint.py` `main()` argv dispatch; option parsing per `docs/cli-reference.md`.
  - Acceptance: `acquire` prints only the id on stdout; `release`/`heartbeat` are idempotent no-ops on missing leases; exit codes match the reference.
  - Docs: `docs/cli-reference.md`.
- [ ] Kind: verification | Status: todo | Exercise the CLI end-to-end without the tray: acquire → list → heartbeat → release, plus idempotency and bad-arg exit codes.
  - Outcome: Proven CLI contract independent of the GUI.
  - Surface: manual/scripted run against a temp `XDG_RUNTIME_DIR`.
  - Acceptance: Every row of the `cli-reference.md` behavior table reproduces; no GUI process spawned.
  - Docs: `docs/cli-reference.md`.

### Phase 3: Tray Integration (reference-counted inhibitor + live menu)

- Phase status: todo

- [ ] Kind: implementation | Status: todo | Make the inhibitor reference-counted: hold one `systemd-inhibit` while `lease_count > 0`; `_refresh()` derives from the lease set; `Gio.FileMonitor` on the leases dir triggers refresh.
  - Outcome: Machine stays awake iff at least one lease is live; state tracks the filesystem.
  - Surface: `sodamint.py` (`start`/`stop`/`is_on` → lease-set model, FileMonitor wiring).
  - Acceptance: Creating/removing lease files from the CLI flips the inhibitor and repaints the tray without manual action.
  - Docs: `docs/tray-ux.md`, `docs/watch-mode.md`.
- [ ] Kind: implementation | Status: todo | Dynamic tray menu: status header, one row per lease (context + age + submenu with liveness + Release), manual toggle as a lease, quit-with-active-leases warning. Both backends.
  - Outcome: The tray shows who holds the machine awake and lets the user release a source.
  - Surface: `sodamint.py` `_build_menu()`/`_refresh()`; AppIndicator `set_menu()` rebuild + StatusIcon fallback.
  - Acceptance: Lease list renders and updates on both AppIndicator and `Gtk.StatusIcon`; manual toggle creates/removes a `manual (tray)` lease; quit warns when leases are active.
  - Docs: `docs/tray-ux.md`.
- [ ] Kind: verification | Status: todo | Drive the tray with live leases and confirm the UX contract on both backends.
  - Outcome: Verified reference-counting + menu behavior.
  - Surface: run the app; create/remove leases via CLI; observe icon, list, manual toggle, quit warning; check `systemd-inhibit --list`.
  - Acceptance: Icon active iff leases > 0; per-source Release works; quit warning appears only with active leases; inhibitor present/absent as expected.
  - Docs: `docs/tray-ux.md`.

### Phase 4: Watchdog & Liveness

- Phase status: todo

- [ ] Kind: implementation | Status: todo | Watchdog timer (default 60s) evaluating PID (+start-time guard), watch-file mtime, and heartbeat; auto-release dead leases; startup reconciliation before acquiring the lock.
  - Outcome: Dead/stale sources are pruned automatically; a restart never re-holds the lock for dead leases.
  - Surface: `sodamint.py` (`GLib.timeout_add_seconds`, liveness checks, startup pass).
  - Acceptance: Killed PID → pruned within a tick; stale watch-file/heartbeat → pruned within `stale_after`+tick; reused PID detected via start-time.
  - Docs: `docs/watch-mode.md`.
- [ ] Kind: verification | Status: todo | Validate the full edge-case matrix from `watch-mode.md`.
  - Outcome: Confidence that the overnight "sleep once work stops" promise holds.
  - Surface: scripted scenarios — hard crash, hang (stale file), manual quit with leases, manual tray release, same-id re-acquire, daemon-down-then-restart.
  - Acceptance: Each matrix row cleans the lease via the documented owner within the documented window; no spurious releases under clock skew.
  - Docs: `docs/watch-mode.md`.

### Phase 5: Wrapper, Docs, End-to-End

- Phase status: todo

- [ ] Kind: implementation | Status: todo | `run --context ... -- <cmd>` scope-guard wrapper (acquire → run → release on any exit); update `CLAUDE.md` to the lease-set source-of-truth model; refresh `install.sh`/README if needed.
  - Outcome: Leak-proof agent integration + docs that match the new architecture.
  - Surface: `sodamint.py` (`run` subcommand), `CLAUDE.md`, `install.sh`/README.
  - Acceptance: Wrapper releases the lease on success, failure, and signal; `CLAUDE.md` no longer claims `self.proc` is the single source of truth.
  - Docs: `docs/cli-reference.md`.
- [ ] Kind: verification | Status: todo | Whole-feature run mimicking the real workload: two parallel "agents" (one via `run --`, one via acquire+heartbeat) plus the manual toggle; kill one; confirm the machine only sleeps after the last lease clears.
  - Outcome: End-to-end proof against the epic's desired outcome.
  - Surface: live app + two simulated agents + `systemd-inhibit --list`.
  - Acceptance: Awake while any lease lives; tray shows all three; killed agent auto-pruned; inhibitor released only when all leases are gone.
  - Docs: `docs/problem-framing.md`, `docs/watch-mode.md`.
