# AGENTS.md

Guidance for automated agents (and any script) working in this repo.

## Keep the machine awake while you work

If your task must not be interrupted by idle/suspend, hold a systemd-logind
inhibitor for the duration of the work. This is a plain `systemd-inhibit` call —
it needs nothing from Sodamint. Sodamint only *reads* these inhibitors and
**highlights** the ones that use the `sodamint-agent` marker, listing them first
in its tray under an `Agents` header.

### Preferred: wrap your command

logind holds the machine awake while the command runs and **auto-releases when
it exits for any reason** (success, failure, crash, `kill`) — nothing to leak.

```bash
systemd-inhibit \
  --what=idle:sleep \
  --who="sodamint-agent" \
  --why="<tool> · <project> · <task>" \
  --mode=block \
  -- <your-command> [args...]
```

Example:

```bash
systemd-inhibit --what=idle:sleep --who="sodamint-agent" \
  --why="epic-loop · sodamint · impl Phase 5" --mode=block \
  -- python3 run_long_agent.py
```

### The contract (what Sodamint keys off)

| Field | Value | Rule |
| --- | --- | --- |
| `--what` | `idle:sleep` | Must include `idle` and/or `sleep`, or Sodamint's filter won't list it at all. |
| `--who` | `sodamint-agent` | **The marker.** Exact, lowercase, literal. Sodamint highlights (`◆`) any inhibitor whose `who` equals `sodamint-agent`; anything else shows as a plain source. |
| `--why` | `<tool> · <project> · <task>` | The row label. Use ` · ` (space, U+00B7 middle dot, space), up to three fields, most-specific last. Free text is fine; keep it to one line. |
| `--mode` | `block` | Hard block, not `delay`. |

`why` fields: **tool** (`epic-loop`, `nightly-build`, `rsync`), **project**
(repo/dir short name), **task** (the specific unit of work). A single free-text
field is valid too — the marker in `who` is what drives highlighting.

### If you can't wrap a single command

For a session that isn't one command (e.g. an interactive loop), hold the lock
explicitly and release it yourself:

```bash
# acquire: start a detached holder, remember its pid
systemd-inhibit --what=idle:sleep --who="sodamint-agent" \
  --why="epic-loop · sodamint · overnight session" --mode=block \
  -- sleep infinity &
hold_pid=$!

# ... do work ...

kill "$hold_pid"   # release when done
```

Prefer the wrap form — the explicit form can leak an orphaned `sleep infinity`
if the agent dies without running its `kill` (logind still auto-releases it if
that orphan is later killed or the machine reboots).

## What Sodamint does with this

- **Lists** the inhibitor (it matches the idle/sleep filter).
- **Highlights** it as an agent source because `who == sodamint-agent`, grouped
  first under `Agents`.
- **Shows** `why` as the row label plus the `pid`.
- Does **not** offer to drop it — external sources are **read-only**. To stop it,
  kill the process yourself or let it finish; logind releases it on exit.

`sodamint-agent` is the stable marker; it must stay in lockstep with `AGENT_WHO`
in `sodamint.py`. The full design is in
[`.epic-loop/epics/multi-source/docs/agent-integration.md`](.epic-loop/epics/multi-source/docs/agent-integration.md).
