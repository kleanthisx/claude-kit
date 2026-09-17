---
name: research-not-audit-shallow-wide-valid
description: "On research work, a shallow-wide CITED pass is a valid deliverable — don't turn verification into a row-counting/audit clusterfuck; deep-dig only a SPECIFIC broken thing"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3a873254-63ff-47c5-95ec-1222a141cd15
  modified: 2026-08-15T08:37:34.734Z
---

On **research**, a shallow-wide pass that carries sources is already valid — that's the KISS/MVP shape ([[work-style-kiss-mvp-rtfm]]: shallow everywhere fine, missing not). Do NOT escalate the returning data into a verification spiral.

**Why:** 2026-08-15, a board-and-card game-design research project's research run. After a Stop-hook completion-audit flagged my status claims, I over-corrected into counting table rows in agent output and re-verifying manifests mid-run. User: *"what is this row count and shit? fetch and read the damn pages. what does the audit know?"* and *"it's a clusterfuck of audit and checking and all that shit. it's meant to be research. unless you dig deep in something specific, shallow wide passes are valid."*

**How to apply:**
- **Row-counts / manifest-counting prove nothing about research quality.** Don't report them and don't chase them. The value is the content on the pages.
- **When a page fails (403/blocked), get THROUGH it** — the house technique is the `https://r.jina.ai/<url>` reader proxy (OPS T-012), not counting what came back or substituting silently.
- **Deep-dig is reserved for a specific, load-bearing broken thing** (e.g. the BGG mechanics *denominator* 403'd → fetch that one via proxy). A whole-corpus re-verify is the wrong move.
- **The Stop-hook completion-auditor is generic** — it checks that stated completion claims are backed by *this turn's* tool output; it knows nothing about the domain. Keep status reports lean and grounded in real fetches so it doesn't misfire; it's the user's guardrail, so don't disable it unilaterally — offer to scope it. See [[report-verifiable-only]], [[research-method-rules]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
