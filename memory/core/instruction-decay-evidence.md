---
name: instruction-decay-evidence
description: "Sourced findings on why standing directives decay in long sessions — write rules as requirements, re-inject after compaction, treat depth-in-session as the risk variable"
metadata: 
  node_type: memory
  type: reference
  originSessionId: cd191791-1c12-4340-a661-8cbdfbe32781
  modified: 2026-08-11T15:27:18.710Z
---

Measured findings on WHY directives decay. **These are the reason the other memory files are phrased as requirements rather than prohibitions.** For what actually WORKS, see [[enforcement-approaches-evidence]]. Full rows + negatives: `projects\LLM-ADHERENCE-RESEARCH.md`.

**1. Commission survives, omission decays.** Omission-type constraints ("never do X") fell from **73% compliance at turn 5 to 33% by turn 16**; commission-type ("always do X") held at **100%**. → Phrase every rule as an action to perform.
[arXiv 2604.20911](https://arxiv.org/html/2604.20911v1)

**2. File structure is not the lever.** A factorial experiment over **1,650 Claude Code CLI sessions** (Sonnet 4.6 + two other frontier models, two TypeScript codebases, five tasks) manipulated file size, instruction position, file architecture, and contradictions between adjacent files. **None produced a detectable effect** after multiple-testing correction, with affirmative-null Bayes factors for size and conflict. → Rewriting, reordering or restructuring CLAUDE.md has no measured benefit; spend the effort elsewhere.
[arXiv 2605.10039](https://arxiv.org/abs/2605.10039) — McMillan, 11 May 2026

**3. Depth into the session is what predicts failure.** Same study: each additional function generated carries **~5.6% lower odds of compliance** per step (OR = 0.944). → Treat turn depth as the risk variable; re-state the operative rule when deep in a session.

**4. Compaction silently deletes constraints.** Violations rose from **0% with the policy in full context to 30% after compaction**, and **59%** on some models — the agent does not know the rule was removed.
[arXiv 2606.22528](https://arxiv.org/abs/2606.22528)

**5. The mitigation with evidence behind it is re-injection, not better authoring.** Constraint pinning (re-inject the policy after every compaction) and a per-model "Safe Turn Depth" threshold past which compliance is treated as unreliable. → Favour engineering controls (hooks, gates, re-injection) over administrative ones (files, recitation).

**Gaps:** read from abstracts and indexed summaries, not full texts. The AgentSpec runtime-enforcement paper would not parse and ACM Queue returned HTTP 403, so the enforcement-mechanism literature is unsourced. Also see [When Models Can't Follow (256 LLMs)](https://arxiv.org/abs/2510.18892) and [Prospective Memory Failures in LLMs](https://arxiv.org/pdf/2603.23530), both unread beyond summary.

**Why:** 2026-08-11 — user observed that written directives keep failing and asked what the scholars had found. My first answer was recalled safety-science names with no sources; this is the fetched version.
