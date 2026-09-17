---
name: work-via-agents-stay-available
description: "Run every heavy/long step (downloads, image gen, edit passes, multi-second scripts) in a subagent or background — keep the main thread free to pilot interactively and to catch \"stop\" instantly"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2b949011-e81f-4b2d-9ee6-f276f7141fbe
  modified: 2026-08-22T07:27:11.138Z
---

The user (2026-08-22): "we do all the work with agents since i need you available to pilot with me. when i said stop i had to wait for the script to finish before you picked it up." A foreground script had blocked the main thread — his "stop" wasn't picked up until the running cost-check call returned.

**Why:** he pilots interactively during creative/infra work and needs the main loop responsive at ALL times — to steer, correct, or halt mid-run without waiting on a blocking call. A long foreground command makes me deaf to him until it finishes.

**How to apply:** dispatch downloads, image/sound gen, Edit-model passes, benchmarks, and any multi-second script to a subagent (Agent tool) or `run_in_background`, then return to the conversation immediately. Never run a long foreground command in the main thread during a piloting session. Match the model to the job (cheap tier for fetch/mechanical). Report results when the agent reports back. Ties to [[bound-the-user-facing-blast-radius]], [[prefer-sonnet-for-subagents]], [[ops-ticket-protocol]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
