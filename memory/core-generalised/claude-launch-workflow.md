---
name: claude-launch-workflow
description: How the user prefers to launch and run Claude Code (project-agnostic)
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5e1d841c-7221-492a-b993-5e469f699f67
  modified: 2026-07-24T16:03:15.336Z
---

The user runs Claude Code **interactively with permission prompts bypassed** — they want
to chat and steer live while Claude acts without tool-approval gates, and Claude should
pause to ask only when things get genuinely risky/hairy. (This preference originated on
a now-delivered pipeline project but applies to all projects.)

**Why:** they value momentum (no per-action approval clicks) but still want a human in the
loop for high-stakes decisions (e.g. force-killing processes, replacing a `.git`).

**How to apply:** default launch is interactive, not headless `-p`. A saved launcher exists
at `C:\Users\<you>\<project>-headless.ps1`, named after that pipeline project (no args = interactive
`claude --dangerously-skip-permissions` from the project dir; pass a prompt for a one-shot headless
run) — despite the project-specific name it works from any directory. They also want to drive it
remotely from phone/work.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
