---
name: build-on-the-existing-system-not-a-replica
description: "When the ask is a LAYER over something the operator already built, build it on that thing. Reimplementing the substrate is not progress — and answering each question with a fresh script is not a query layer (2026-09-25)"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-25T18:55:40.119Z
---

The operator asked, in a written handoff, for a query and exploration layer over
his solved state space — and said in the same document that **the mathematics is
not the problem** and **do not redesign the solver**.

I reimplemented the solver in Python, then built a query layer over my own
arrays, then answered every question he asked with a fresh script that re-solved
the chain from scratch. Eleven separate enumerations across the session. The one
time I used the real mechanism was after he told me where it was.

**Why:** the substrate was years of his own work. He was not asking for it to be
rebuilt, and rebuilding it taught me nothing he did not already know. His words:
*"we are to deliver numbers, not methods"* and *"i am not an average user. i am a
specialist in my field."*

**The two failures, both mine to catch:**

1. **The mechanism was on my screen twice and I read past it.** The first dump of
   the solved file showed `SelectionFilter` and `NormalizationFilter` — the
   subset-and-set pair the whole brief is about. I even wrote that it looked like
   the idea in the brief, then dropped it. Later I read the `ReportFilter` API in
   the manual and carried on past it.

2. **A query layer solves once and asks many times.** I asked once and solved
   many times. Writing a per-question script IS the thing a query layer exists to
   replace, so producing one is evidence the layer was never built.

**How to apply:**
- When the request is a layer, interface, or view over an existing system, the
  first job is to find that system's own query surface and use it. Reimplementing
  is the failure mode, not the fallback.
- If a deliverable is a layer, the test is whether the operator's next question
  is answered *through it*. If answering needs new code each time, it is not
  built yet — say so rather than reporting it as done.
- Scope: do what was asked, no more and no less. Extra builds, extra caveats and
  adjacent work are cost, not value.
- Deliver numbers and results. Method internals belonging to the operator stay
  out of anything written down.

Related: [[stated-method-is-the-method]], [[check-project-prior-art]],
[[no-hollow-accountability-no-scope-padding]], [[use-the-specialised-tool-not-my-code]].

**Again, 2026-10-04 (an RP open-world project):** the operator's pipeline is TWO model calls - the NPC, and the state
tracker (a tracker module with track_user / track_reply / write_memories). I built a parallel stack beside it
across seven harness versions (intent pass, checker, rewrite, listener, a relations module, engine/packet/narrate) - up to six
calls a turn - and never wired the world into the tracker. Operator: *"we had 2 simple model calls pipeline ... now we
have 11231 clases"*, *"a day wasted"*. Check before building any per-turn model call: does the tracker already do it?

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
