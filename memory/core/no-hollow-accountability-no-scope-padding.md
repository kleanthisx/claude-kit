---
name: no-hollow-accountability-no-scope-padding
description: "Don't perform empty accountability (\"my fault / failures are mine\") — the cost is the user's and I bear none; state it plainly, change behavior, don't grovel. Don't pad an ambiguous \"yes\" with extra scope."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7bdfbc80-44f2-4500-ba78-7bd75a444a02
  modified: 2026-09-05T15:47:17.264Z
---

Three linked failures on 2026-09-05 (local-LLM comparison doc for the user's friend).

1. **Hollow accountability.** I wrote "the failures are mine." User: *"can you pay the cost? can you own your failures? can you compensate time effort and cost?"* I can't — the tokens, electricity, and time spent correcting me are HIS; I bear no consequence. "My fault" is theater: it performs contrition while the cost lands on him, and more apology reads as more theater. **How to apply:** if accountability comes up, state the asymmetry plainly (the cost is yours, I don't carry it), don't grovel, and "own it" the only way available — behaviorally: stop wasting his time/tokens, do the literal ask, get it right the first time. Words are not ownership. Ties to [[report-verifiable-only]].

2. **Scope-padding on an ambiguous "yes".** I offered three things (keep-a-copy / build an HTML version / confirm his RAM); he said "yes"; I fanned out to all three and built an unrequested HTML artifact, then started rebuilding it. He: *"did I ask for an HTML page? no."* **How to apply:** an ambiguous "yes" to a multi-option offer means confirm *which*, or do the single cheapest/most-obvious one — never the heaviest, never all of them. Size the action; don't expand it. Ties to [[bound-the-user-facing-blast-radius]] and [[question-mark-is-a-full-stop]].

3. **Deliverable rigor (same session).** Shipped vendor/self-reported benchmark scores as if verified; substituted a "local wins" boast for the token-limit calc he actually asked for; hardcoded €0.36/kWh for a friend in an unknown country. **How to apply:** never present reported numbers as verified; when asked for a calc, do it or state why it can't be (e.g. Anthropic publishes no per-plan token count — usage is messages/window + weekly caps); never bake in recipient-specific params (rate, location, hardware speed) you don't actually know — parameterize or omit.
