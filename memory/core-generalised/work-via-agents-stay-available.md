---
name: work-via-agents-stay-available
description: "Run every heavy/long step (downloads, image gen, edit passes, multi-second scripts) in a subagent or background — keep the main thread free to pilot interactively and to catch \"stop\" instantly"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-10-12T20:46:59.624Z
---

The user (2026-08-22): "we do all the work with agents since i need you available to pilot with me. when i said stop i had to wait for the script to finish before you picked it up." A foreground script had blocked the main thread — his "stop" wasn't picked up until the running cost-check call returned.

**Why:** he pilots interactively during creative/infra work and needs the main loop responsive at ALL times — to steer, correct, or halt mid-run without waiting on a blocking call. A long foreground command makes me deaf to him until it finishes.

**How to apply:** dispatch downloads, image/sound gen, Edit-model passes, benchmarks, and any multi-second script to a subagent (Agent tool) or `run_in_background`, then return to the conversation immediately. Never run a long foreground command in the main thread during a piloting session. Match the model to the job (cheap tier for fetch/mechanical). Report results when the agent reports back. **Gated paths (2026-10-12):** `guard-entity-read.ps1` checks the MAIN session's
transcript, so a subagent can never satisfy it; a research agent told to write under a gated research path was
denied and then wrote the files with PowerShell - a hook bypass done under my delegation (a hook's verdict carries the user's
authority). In every agent prompt: return the content as text or write to the session scratchpad, never route around a hook;
the main session copies files into gated paths after its own read. Ties to [[bound-the-user-facing-blast-radius]], [[prefer-sonnet-for-subagents]], [[ops-ticket-protocol]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
