---
name: check-project-prior-art
description: "Search the project for prior art (runbooks, measured numbers, existing scripts) BEFORE external research or estimating"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d542eff2-17f5-493c-82b0-e6f9e960faaf
  modified: 2026-08-06T21:06:47.570Z
---

When costing/designing anything, grep the project tree for prior art first — runbooks, measured benchmarks, existing scripts — before web research or first-principles estimates.

**Why:** 2026-08-06, a large story archive processing costs: I estimated rented-GPU throughput from scratch and priced a two-pass pipeline, while `an RP project/classify/CLOUD_RUN.md` already held MEASURED throughput (266 ch/hr per rented GPU), a superseding single-pass extractor (extract.py), and automated box setup. User had to point it out ("there's info in the project"). The measured numbers changed the recommendation materially (~$150 estimate → ~$1.5k reality for full-rich).

**How to apply:** before answering cost/feasibility/design questions in an existing project, run a quick Grep for related keywords (tool names, "RUN", "PLAN", "HANDOFF", *.md runbooks) and read what exists. Estimates only where no measurement exists — and say which is which. Related: [[work-style-kiss-mvp-rtfm]] (RTFM applies to the user's own repos too), a related note.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
