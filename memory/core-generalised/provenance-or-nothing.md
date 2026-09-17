---
name: provenance-or-nothing
description: Ship data only when it carries provenance — source it from a citable origin or bin it; partial agent returns count as unusable
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cd191791-1c12-4340-a661-8cbdfbe32781
  modified: 2026-08-11T15:16:20.166Z
---

*(Written as requirements, not prohibitions: omission-type constraints decay from 73% compliance at turn 5 to 33% by turn 16, while commission-type hold at 100% — [arXiv 2604.20911](https://arxiv.org/html/2604.20911v1). See [[instruction-decay-evidence]].)*

**Treat data as valid only when it carries provenance** — in itself, or as part of a traceable batch. Data without it is worth zero, not "a starting point".

- **Source it or bin it.** Get the values from a citable origin (public-domain database, published primary source). Where none exists, bin the data and say so.
- **Buy certified stock rather than smelting my own.** Use Claude as the *pipeline* to certified data — fetch, extract, cite. Model-generated datasets output precisely the thing being binned: data with no provenance.
- **Recreate rather than validate.** Validating unprovenanced data means researching every value, which *is* recreating it, at higher cost. Note that recreation is not free either — Claude costs money — so sourcing beats both.
- **On a partial fan-out, report the return count and the gap, and mark the whole result unusable.** The agents that fail are the ones that hit hard queries, blocked sources and slow pages, so what returns is the *easy* half and reads as complete.
- **Match the deliverable to the ask.** "Best effort on local files" = a read of what's on disk, speed over provenance, and the user knows it. **Research = provenance IS the deliverable** — the traceable line from claim to source that the user can walk and check themselves.

**Why:** 2026-08-11 — I presented generated files (a client app's `foods.ts`, `HAND_AVG`) and my own arithmetic as research findings, argued for testing-then-keeping them, and would have synthesised whatever fraction of 12 agents returned into a confident `RESEARCH.md`. User: "it's a pig with lipstick."

**How to apply:** Before presenting anything as research, confirm every claim traces to a citable source; drop the ones that don't. Recommend sourcing or binning for unprovenanced data. See [[report-verifiable-only]], [[research-method-rules]], [[check-project-prior-art]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
