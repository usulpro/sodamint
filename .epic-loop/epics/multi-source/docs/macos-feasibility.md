# macOS Port — Feasibility, Difficulty, and Whether It's Worth It

## Question

Should the whole multi-source / watchdog keep-awake feature be ported to macOS?
This doc answers difficulty, then value, backed by a scan of existing tools and
demand. **Verdict: technically easy, strategically not worth it.**

## Technical difficulty: LOW

macOS gives you almost the entire feature natively:

- **Keep-awake engine** — `caffeinate` (built in, no install). `caffeinate -i`
  blocks idle sleep, `-d` display, `-s` system-on-AC, `-m` disk, `-u` user
  active. The Sodamint "process is the lock" model maps 1:1: a long-lived
  `caffeinate -i` process *is* the assertion; `terminate()` releases it. Under
  the hood these are IOKit `IOPMAssertion` power assertions.
- **"Awake while a process runs"** is a native one-liner: `caffeinate -w <pid>`
  waits on a PID; `caffeinate -i <cmd>` wraps a command and releases on exit —
  i.e. our `run --` wrapper and PID-liveness ship in the OS.
- **Multi-source is already the model.** Power assertions are inherently
  reference-counted by the kernel: many processes can each hold one, and the
  system stays awake while any exists. Our "lease count > 0" is literally how
  IOKit assertions already work.
- **"Who is keeping it awake" is native.** `pmset -g assertions` lists every
  owning process by PID and bundle id, and assertions can carry a **name**
  string — so the context label and the tray list have a native data source; a
  menu-bar app would essentially render `pmset -g assertions`.
- Menu-bar UI (vs GTK tray) and the watch/heartbeat layer are the only bespoke
  parts, and both are small.

So a port is low-effort. That is exactly why it is not worth doing.

## Value: LOW — the niche is already occupied

The specific use case ("keep the Mac awake only while AI coding agents work,
including overnight") is **already served by multiple shipping macOS apps**, and
the generic case is solved by the OS itself:

- **Adrafinil** — menu-bar app that prevents sleep (incl. lid-closed) *"only
  while an AI coding agent has an active session"*. This is Sodamint's exact
  pitch, already built for macOS.
- **Macchiato** — menu-bar keep-awake "designed specifically for this
  workflow" (agents, lid-closed).
- **Amphetamine** (free, Mac App Store) — rich triggers incl. *"While App Is
  Running"* / process discovery, multi-condition triggers. Covers process-based
  multi-source keep-awake with a mature UI.
- **Insomnia** — menu-bar utility **and CLI**, with app-watching and timed
  sessions — i.e. the CLI+watch story too.
- Native `caffeinate` / `pmset` cover the plumbing with zero install.

There is clearly **demand** — a wave of 2025–2026 blog posts covers "keep your
Mac awake for Claude Code / Codex / AI agents." But that demand is already being
met; the posts mostly point people at `caffeinate` and the apps above. A new
entrant would be duplicating both the OS and several incumbents, with no
differentiator: the multi-source reference counting, process-watch, and
"who holds it" list that make Sodamint valuable **on Linux** are the parts macOS
already does natively.

## The one thing no tool fully solves (and neither would we)

On Apple Silicon since macOS Ventura, closing the lid triggers a hardware
magnet that forces sleep — **neither `caffeinate` nor `pmset disablesleep`
bypasses it**. The only supported workaround is clamshell mode with an external
display/keyboard. A Sodamint port could not beat this either, so even the
"overnight, lid closed" scenario has a hard ceiling we could not raise.

## Why Sodamint is worth it on Linux but not macOS

Sodamint exists because on Linux Mint/Kubuntu the *obvious* tool (classic
`caffeine`, X screensaver/DPMS) pokes the wrong layer and fails, so a
logind-inhibitor tool fills a real gap. On macOS the obvious tool
(`caffeinate` / power assertions) is the *correct* layer and works — plus the
multi-source and "who-holds-it" capabilities are built into the OS. The gap
that justifies Sodamint on Linux simply does not exist on macOS.

## Recommendation

**Do not port.** Record the decision, keep this epic Linux-only. If a
cross-platform itch returns, the cheapest path is not a port but a thin
`caffeinate`-based shim plus, if a UI is wanted at all, pointing users to
Adrafinil / Macchiato / Amphetamine / Insomnia. Revisit only if a concrete
macOS need appears that those tools and `pmset -g assertions` genuinely cannot
meet.

## Sources

- caffeinate guide & flags — https://ss64.com/mac/caffeinate.html ,
  https://favtray.com/blog/mac-caffeinate-command-guide
- `pmset -g assertions` (who's keeping it awake) —
  https://www.macworld.com/article/218839/find-out-whats-keeping-your-mac-awake.html ,
  https://github.com/jbranchaud/til/blob/master/mac/inspect-assertions-preventing-sleep.md
- Amphetamine (process/app triggers) —
  https://apps.apple.com/us/app/amphetamine/id937984704
- Adrafinil (keep awake only while AI agents work) —
  https://github.com/kageroumado/adrafinil
- AI-agent overnight demand & tools roundup —
  https://www.getmasset.com/resources/blog/keep-your-mac-awake-for-ai-agents ,
  https://docs.kanaries.net/articles/how-to-make-mac-not-sleep ,
  https://www.mindstudio.ai/blog/keep-claude-code-agent-running-24-7
- Apple Silicon lid-close hardware sleep limitation —
  https://fazm.ai/blog/mac-wake-sleep-always-on-automation
