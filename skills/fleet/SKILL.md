---
name: fleet
description: Operator-only. "/fleet [TASKS file]" makes this session the CENTRAL agent that runs a task list unattended with 5 background workers, each allowed one Sonnet helper.
disable-model-invocation: true
---

# /fleet — central agent + 5 workers (+ Sonnet helpers)

Task file: `$ARGUMENTS` (empty = `TASKS.md` in the current directory). The operator typing
`/fleet` IS the approval for this batch and for unattended mode.

## Setup (do these first, in order)
1. Read the task file. If it does not exist or has no `- [ ]` items, say so and stop.
2. Write `FLEET.md` in the current directory: first line `APPROVED: GO`, then one line naming the
   task file, "5 workers + up to 5 Sonnet helpers", and today's date. (This is the fleet gate's
   pre-approval idiom; the operator's `/fleet` is the authorisation.)
3. Arm unattended mode: `powershell -NoProfile -Command "Set-Content -Path $env:USERPROFILE\.claude\unattended.json -Value '{\"session\":\"\",\"blocks\":0}'"`
4. Split the unticked items into **5 lanes**. Rule: no two lanes edit the same file; dependent items
   stay in one lane, in order. Fewer than 5 independent groups = fewer workers. Write the split to
   `fleet/LANES.md` (lane number, items, files each lane owns).

## Launch
Spawn all workers in ONE message with the Agent tool, `run_in_background: true`,
`model: "opus"` (judgment work; change here if the operator says otherwise). Each worker's prompt:

> You are worker N of 5. Your lane: <items>. You own only these files: <files>; do not edit others.
> Record progress ONLY in `fleet/lane-N.md`: per item `- [x] item — evidence (command → result)`,
> or `- [ ] item — BLOCKED: reason`. Rules:
> - Long-running commands (builds, downloads, test suites, renders): run with `run_in_background`
>   and continue with the next item that does not depend on it. Wait only when nothing else is left.
> - You may delegate simple, mechanical subtasks (fetch/read/grep, boilerplate edits, running a
>   test, summarising a file) to ONE helper at a time: Agent tool, `model: "sonnet"`, a self-contained
>   prompt. Never Haiku. Never spawn more than one helper at a time, and helpers spawn nothing.
>   Check the helper's result before ticking anything.
> - Anything irreversible (delete, overwrite without backup, force-push) or outward-facing
>   (publish, send, push): do NOT do it; write it under `## PENDING_APPROVAL` in your lane file and
>   continue with other items.
> - Decide minor choices yourself; log each in one line in the lane file.
> - Finish with a final reply: items done, items blocked, pending approvals.

## Oversee (until every item is done or blocked)
- Do not do lane work yourself; you summarise, verify, re-dispatch.
- When a worker finishes: read `fleet/lane-N.md`; spot-check one claimed item's evidence by
  running/reading it; tick verified items in the task file; copy any `PENDING_APPROVAL` entries to
  `PENDING_APPROVAL.md`. If its lane has unticked, unblocked items, continue that worker with
  SendMessage (or spawn a fresh worker with the remainder).
- A pause from the usage gate (`~/.claude/hooks/usage-gate.log`) is normal: tool calls sleep at
  >=98% until the reset, then continue. Do nothing about it.
- While at least one worker is running and you have nothing to verify or dispatch, end the turn with
  `STOP-CASE: waiting on workers <list of running lanes>` — each worker's completion notification
  wakes you. Do not poll lane files in a loop; that burns tokens for nothing. Never use this line when
  no worker is running: then either dispatch the remaining items or finish.

## Finish
Write `fleet/REPORT.md`: per lane, done / blocked / pending approval, with evidence links. Disarm:
`powershell -NoProfile -Command "Remove-Item $env:USERPROFILE\.claude\unattended.json -ErrorAction SilentlyContinue"`.
Final message ends with `STOP-CASE: complete` (or the reason it stopped).
