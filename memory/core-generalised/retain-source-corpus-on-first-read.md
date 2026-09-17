---
name: retain-source-corpus-on-first-read
description: "A research pass must RETAIN the full fetched source text (a corpus) on first read, not distill to summary rows and discard the source — else you pay a second full re-read and lose depth to link-rot"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3a873254-63ff-47c5-95ec-1222a141cd15
  modified: 2026-08-15T10:10:21.612Z
---

On any research fan-out, have agents **save the cleaned full text of each key source to a `corpus/` dir on the FIRST read, then distill.** Do not distill-to-summary-and-discard-the-source.

**Why:** 2026-08-15, a board-and-card game-design research project. First pass = 15 agents wrote one-line cited rows and kept **no** source text. When the user wanted actual *knowledge* (not a citation index), the only way to get it was to re-fetch the same sources a SECOND time to build `corpus/` + a teaching `KNOWLEDGE.md`. User, sarcastic: *"so we read them once and then we read them again… true specialists."* The double-read was pure waste caused by the row-only output format — and the sources that 403'd/died in the interim (see SYNTHESIS §5) can't be re-read at all.

**How to apply:**
- Three fidelity levels: **pointer** (title+URL) / **teaching-summary** (concept in our words) / **captured-source** (the actual article text stored locally). For load-bearing items keep the **captured-source** — indexes and summaries sit ON TOP of a retained corpus, never in place of it.
- Cost of retaining a page you already fetched ≈ one Write. Cost of NOT retaining it = a second full fetch later, or total loss to link-rot. Always retain.
- Reader-proxy `https://r.jina.ai/<url>` beats the 403s for the capture.
- See [[provenance-or-nothing]] (provenance IS the deliverable), [[research-method-rules]] (rows before prose — but keep the source behind the row), [[research-not-audit-shallow-wide-valid]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
