# Keeping The Machine Awake From An Agent

This is the contract an automated agent (or any script) follows to keep the
machine awake for the duration of its work **and** show up as a recognizable
"agent" source in the Sodamint tray. It needs nothing from Sodamint — it is a
plain `systemd-inhibit` call the agent runs via bash. Sodamint only *reads*
these inhibitors and highlights the ones that follow the marker below.

## The one-liner (preferred: wrap your command)

Wrap the long-running work in `systemd-inhibit`. logind holds the machine awake
while the command runs and **auto-releases when it exits for any reason**
(success, failure, crash, `kill`) — no cleanup to leak.

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
  --why="epic-loop · sodamint · impl multi-source Phase 2" --mode=block \
  -- python3 run_long_agent.py
```

## Message-format contract

These fields are the contract. Sodamint keys off `who` and displays `why`.

| Field | Value | Rule |
| --- | --- | --- |
| `--what` | `idle:sleep` | Must include `idle` and/or `sleep`, else Sodamint's filter (D12) will not list it at all. |
| `--who` | `sodamint-agent` | **The marker.** Exact, lowercase, literal. Sodamint highlights any inhibitor whose `who` equals `sodamint-agent`. Anything else shows as a plain (non-agent) source. |
| `--why` | `<tool> · <project> · <task>` | Human label shown as the row text. Use ` · ` (space, U+00B7 middle dot, space) as the field separator, up to three fields, most-specific last. Free text is allowed; Sodamint shows the whole string and, when it splits cleanly on ` · `, may render the fields distinctly. Keep it short — one line. |
| `--mode` | `block` | Hard block, not `delay`. |

Field guidance for `why`:

- **tool** — what is running, e.g. `epic-loop`, `nightly-build`, `rsync`.
- **project** — repo/dir short name, e.g. `sodamint`.
- **task** — the specific unit of work, e.g. `impl multi-source Phase 2`.

Minimal valid `why` is a single free-text field, e.g. `--why="nightly build"`.
The marker in `who` is what matters for highlighting; `why` is for the human.

## If you can't wrap a single command

For a session that is not one command (e.g. an interactive loop), hold the lock
explicitly and release it yourself:

```bash
# acquire: start a detached holder, remember its pid
systemd-inhibit --what=idle:sleep --who="sodamint-agent" \
  --why="epic-loop · sodamint · overnight session" --mode=block \
  -- sleep infinity &
hold_pid=$!

# ... do work ...

# release: kill the holder when done
kill "$hold_pid"
```

Prefer the wrap form when you can — the explicit form can leak an orphaned
`sleep infinity` if the agent dies without running its `kill`. (logind will
still auto-release it if that orphan is itself killed or the machine reboots.)

## What Sodamint does with this

- **Lists** the inhibitor (it matches the idle/sleep filter).
- **Highlights** it as an agent source because `who == sodamint-agent`.
- **Shows** `why` as the row label and the `pid`.
- Does **not** offer to drop it — external sources are read-only (D14). To stop
  it, kill the process yourself or let it finish; logind releases it on exit.

## Contract stability

`sodamint-agent` is the stable marker. If it ever changes, this doc is the
source of truth and Sodamint's highlight match must be updated to agree. Keep
the two in lockstep.
