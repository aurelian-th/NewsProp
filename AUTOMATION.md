# NewsProp Heartbeat Automation

## Purpose
Resume autonomous work on NewsProp without losing context. The automation should wake this thread on a fixed cadence, read `STATE_MACHINE.md`, continue the next intent, update the state file, and keep the research wiki in sync.

## Recommended Heartbeat
- Type: thread heartbeat
- Cadence: every 30 minutes
- Primary loop:
  1. Read `STATE_MACHINE.md`.
  2. Execute the current intent.
  3. Verify outputs and log results.
  4. Update `STATE_MACHINE.md` and `research_wiki/`.
  5. Continue with the next measurable intent.

## Guardrails
- Prefer execution over research; keep research time below 10 percent unless blocked.
- Recover gracefully from failures and log pivots.
- Do not duplicate completed work; trust the state file.
- Keep commits intentional and scoped.
