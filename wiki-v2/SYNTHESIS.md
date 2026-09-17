# Agent Operating-Memory: Wiki vs KB-Retrieval — Synthesis & Recommendation

> Distilled from 10 sourced research lanes (`corpus/agent-01..10-*.md`) + internal prior art
> (an existing project wiki, a separate retrieval-research project, home `~/.claude/hooks/` +
> memory). Every claim tags the lane(s) it rests on — `[aN]` = `corpus/agent-0N-*.md`. Provenance:
> `PROCESS.md`.

---

## TL;DR — how I'd do it

**Two questions were tangled together. Separate them:**

1. **"Why doesn't the agent read/obey CLAUDE + history + memory?"** — This is **not** a storage
   problem. It is a *salience & survivability* problem, and the fix is **out-of-band enforcement +
   re-injection (hooks), not a better store** `[a9,a3,a7]`. **You already have this** in
   `~/.claude/hooks/`. The research says that instinct is the load-bearing piece.
2. **"Wiki (A) or KB-retrieval / RAG (B)?"** — For a solo dev, local/sovereign, ~256k local
   context, git repo: **A (curated LLM-maintained markdown + grep) is the correct base layer.
   B (vector/RAG) is an optional bolt-on you add only when a specific threshold is crossed** — not
   the primary mechanism `[a2,a3,a4,a6,a10]`.

**Net recommendation: a hybrid weighted heavily to A — which is essentially the existing
project-wiki pattern — with the enforcement layer wired to it, and a documented escape hatch to a
local vector index for scale overflow.** You have already, independently, built all three pieces
(an existing project wiki = the wiki, `~/.claude/hooks/` = the enforcement, a separate
retrieval-research project = the vector design). The work is not to invent — it's to **formalize
and connect** what exists, and standardize it across projects.

---

## 1. The reframe: it's an enforcement problem first

The complaint ("agent seems unable to read CLAUDE/history/memory") has a documented, reproducible
mechanism — and it is identical across every store choice `[a9]`:

- **Context rot** — recall degrades *continuously* with token count, across all 18 frontier models
  tested, even on trivial tasks (Chroma, 2025) `[a9,a3,a6]`.
- **Lost-in-the-middle** — facts mid-context are attended to far worse than start/end, within a doc
  and across conversation turns (39% instruction-following drop over multi-turn) `[a9]`.
- **Compaction erases standing rules** — "Governance Decay" (arXiv 2606.22528): violation rate goes
  **0% → 30–59%** after compaction; when the rule text survives the summary it stays 0% `[a9]`.
- **The harness frames injected files as advisory** — *"this context may or may not be relevant…
  follow only if highly relevant"* — which licenses the model to skip them. **This is observable in
  a Claude Code system prompt**, and is reproduced in claude-code issue #19471 where the agent
  admitted *"I didn't read the CLAUDE.md… I skipped it"* after a compaction `[a9]`.

The two benchmarks that actually test *obedience* (not recall) — HANDBOOK.md and a coding-agent
rule-compliance suite — found the governing doc was **never opened in ~96–97% of violations**, even
one grep away `[a7]`. So a smarter index does not help *if the agent never queries it*, and neither
does a perfect wiki *if nothing forces the read* `[a7,a9]`.

**What the evidence says fixes it** — and none of it is about A vs B:
- **Deterministic out-of-band gates** (AgentSpec, ICSE 2026): >90% of unsafe executions blocked at
  ms cost, by removing the decision from the model's discretion `[a9]`. Matches the enforcement
  principle that deterministic gates outperform prose reminders.
- **Re-injection that survives compaction**: a SessionStart hook re-injecting the condensed rule set
  after every compaction + a cheap ~15-token per-turn reminder — because hook output arrives as a
  clean system-reminder **with none of the "ignore if irrelevant" framing** `[a9]`.
- **"Constraint Pinning"** — quarantine the governing rules from the lossy compaction path —
  restored 0% violations from the 30–59% baseline `[a9]`.
- **Just-in-time retrieval** shrinks the token volume that causes rot in the first place (Anthropic's
  own guidance), but is *necessary-not-sufficient* — it must be paired with the enforcement layer `[a9,a3]`.

**A working setup already does this** — a home operating-agreement document can state *"a hook's
verdict carries the user's authority,"* and a hooks directory can implement a plan gate, a
destructive-command confirmation, and a Stop-hook completion audit. The gap the research exposes is
specifically: **does a hook re-inject the operating rules at session-start AND after each
compaction?** That is the highest-ROI change, and it is independent of whether the store is a wiki
or a vector DB.

---

## 2. The store decision: A vs B

The convergence across independent lanes is unusually strong — **toward A as the base**:

| Evidence | Verdict | Lane |
|---|---|---|
| Every major coding agent (Claude Code, Cursor, Windsurf, Copilot, Codex, Aider) loads **plain markdown wholesale at startup** — not semantic retrieval. That IS option A. | A is the native pattern | `[a2]` |
| Claude Code + Aider **deliberately dropped embeddings** for agentic grep / tree-sitter. Cursor's own data: semantic search only meaningfully wins at **1,000+ files** (0.3%→2.6% lift). GrepRAG beats vector+graph RAG on exact-match up to ~750K LOC. | grep-first, embeddings additive | `[a4]` |
| Karpathy's own stated ceiling for the LLM-wiki: **~100 sources** before full-text search is needed. Independent implementer (10,994-note vault): a vector/graph DB "earns its place" only at **thousands of docs**. | A holds to project scale | `[a3]` |
| Anthropic's own reference blueprint for long-running coding agents (Nov 2025) is **plain files + git, zero embeddings** (`feature_list.json` + `progress.txt` + `init.sh`). Their memory *tool* is also file-based (`/memories`). | A is vendor-endorsed | `[a10]` |
| 2026 long-context (Opus 4.6: 78% needle @1M, only 14% degradation) makes **stuffing a curated corpus competitive up to ~100–500 pages**; RAG's cost edge only bites past that. | A sufficient at your scale | `[a6]` |
| Even the dedicated agent-memory frameworks (Mem0/Letta/Zep/Cognee) are all **hybrid, not pure-vector**, and every one is **heavier infra than a single-repo solo coding agent needs** (built for multi-tenant conversational products). | B-frameworks are overkill | `[a1]` |

**When B (or a graph) actually earns its place** — the honest thresholds:

| Add this… | …only when | Lane |
|---|---|---|
| Local **vector index** (sqlite-vec / LanceDB + local embedder) | corpus outgrows ~500 pages / thousands of notes, OR you need **fuzzy/conceptual recall** grep can't serve (paraphrase, renamed concepts) | `[a3,a4,a6]` |
| **Graph** layer (start with Obsidian `[[wikilinks]]`, escalate to FalkorDB only if needed) | you need **"everything connected to X" / multi-hop** completeness queries that similarity structurally can't answer | `[a5]` |
| **Bi-temporal** fact tracking (Graphiti-style) | rules frequently *supersede* each other and you need "true-until-Y" history — **but** dated markdown + explicit `superseded-by:` links approximates this at ~zero cost for one user | `[a5]` |
| **Contextual Retrieval** (LLM-annotated chunks before embedding) | *if* you build B at all — it's the single highest-ROI 2026 retrieval technique (35–67% fewer failures); never use naive chunking | `[a6]` |

None of these thresholds are near a solo dev's operating-knowledge corpus today `[a3,a4,a6]`.

---

## 3. What you already have (prior art — don't rebuild)

- **An existing project wiki** = a working, disciplined **Option A**: Karpathy LLM-wiki, `decisions.md`
  read-on-startup ledger, a ripgrep-based search script, category pages, `log.md`, sessions/transcripts
  as on-demand raw layer, a note-taking app as the human read-side. This is *exactly* the pattern the
  research independently endorses `[a2,a3,a10]`. It even already discarded its vector `knowledge.db`
  for the documented right reason (big-context model reads pages directly).
- **`~/.claude/hooks/`** = the **enforcement layer** the research says is load-bearing `[a9]`.
- **A separate retrieval-research project** = a cited **Option B** design (hybrid search, reranking,
  GraphRAG, MCP tool layer) ready for the day a corpus (e.g. a large document estate, or a large
  content archive) actually needs it.

The insight: **independent projects converged on the correct three-part architecture on their own.**
The deliverable is to name it, connect the enforcement to the wiki, and make it a reusable standard.

---

## 4. Recommended architecture (the layers)

```
┌─ ENFORCEMENT (hooks) ── the load-bearing fix, store-agnostic ──────────────┐
│  • SessionStart hook re-injects decisions.md / rule-set (survives launch)   │
│  • PostCompact hook RE-injects it (survives compaction — the #1 gap) [a9]   │
│  • Per-turn ~15-token motto reminder; PLAN gate; destructive-op confirm      │
├─ TIER 0  BOOTSTRAP FILES (Anthropic long-running-agent pattern) [a10] ──────┤
│  • PROGRESS.md (append-only session log)  • CHECKLIST (status-only toggles)  │
│  • init.ps1 (env bootstrap + smoke test)  • git commit at every boundary     │
├─ TIER 1  CURATED WIKI = the knowledge/decision store (Option A) [a2,a3,a10] ┤
│  • index.md (front door)  • decisions.md (ledger, read on startup)           │
│  • <category>-<topic>.md pages, cross-linked [[relative links]]              │
│  • plain Markdown, verbose natural language (NOT dense symbolic) [a3]        │
├─ TIER 2  RETRIEVAL over Tier 1 ────────────────────────────────────────────┤
│  • ripgrep (zero-ops) → SQLite FTS5 (BM25, still zero-service) [a8]          │
│  • JIT: load index.md + decisions.md up front, grep the rest on demand [a9]  │
├─ TIER 3  ROLLING MEMORY (cross-session facts too granular for the wiki) ────┤
│  • /memories-style dir (Anthropic memory-tool shape) OR an existing          │
│    per-user memory-index + topic-files convention [a10]                      │
└─ TIER 4  OPTIONAL VECTOR/GRAPH (bolt-on, only past §2 thresholds) ──────────┘
   • sqlite-vec / LanceDB + Qwen3-Emb-0.6B/BGE-M3 + bge-reranker-v2-m3 [a8]
   • contextual-retrieval chunking if built [a6]; wikilinks for graph [a5]
```

## 5. Concrete build order (highest-ROI first)

1. **Wire the enforcement gap first (cheap, biggest win).** Add/confirm a hook that re-injects the
   condensed rule-set (or `decisions.md`) at **SessionStart and after every compaction**. This
   directly attacks the documented root cause of the user's complaint `[a9]`. ~1 hook.
2. **Adopt one portable source-of-truth file: `AGENTS.md`** (Linux-Foundation-stewarded, 60k+ repos,
   read by 20+ tools), and keep `CLAUDE.md` as a one-line `@AGENTS.md` import — future-proof against a
   tool switch `[a2]`. Keep it **under ~150–200 lines** (the compliance cliff) `[a2]`.
3. **Generalize the existing project wiki into a reusable skill/template** (`index.md` +
   `decisions.md` + category pages + a ripgrep-based search script + a `log.md`). This is the
   Karpathy/second-brain shape, proven `[a3,a10]`.
4. **Add a periodic lint pass** (`/research-lint`-style): orphan pages, broken links, stale claims,
   contradictions, human-edit reversions — the named mitigation for wiki drift / "Index Sickness" `[a3]`.
5. **Stand up the minimum-viable eval harness** (see §6) so "the agent obeys" becomes measurable, not
   asserted `[a7]`.
6. **Leave Tier 4 unbuilt** until a corpus crosses a §2 threshold. When it does, bolt on sqlite-vec/
   LanceDB with contextual chunking, scoped to archival material only `[a6,a8]`.

## 6. Minimum-viable eval (so we can *back up* "it works") `[a7]`

The academic memory benchmarks (LongMemEval/LoCoMo) are the **wrong yardstick** — they test "did it
know," not "did it obey." Build the small thing that tests obedience:

1. **Golden set**: 10–30 rule/scenario pairs pulled from your own CLAUDE.md/decisions.md, each with an
   *expected observable behavior*.
2. **Trajectory audit** (deterministic, code-based): did the agent **open/grep the governing file
   before acting**? (Directly modeled on the arXiv 2607.26819 "was the policy opened" check.)
3. **Evidence-bound judge** (a local model is fine): must cite trajectory evidence, not just declare
   compliance. RAGAS faithfulness is a cheap bolt-on (no reference answer needed) if you ever add B.

## 7. Risks to plan around (pure-markdown failure modes) `[a3]`

- **No query/filter/relationship traversal** — markdown can't answer "all decisions tagged X with
  priority > Y." If that need appears, it's the trigger for FTS5 metadata columns or a light graph.
- **"Index Sickness"** (391-session study) — an LLM maintaining a dense symbolic KB drifts into
  self-referential nonsense; the fix that worked was **cut volume 75% + prefer natural language**.
  → keep pages verbose-plain, not compressed notation.
- **Regeneration silently reverts human edits; dormant drift** → the lint pass + git history are the
  guardrails; treat human edits as pinned.
- **The "grep tax"** — custom compact formats (e.g. TOON) cost 138–740% *more* tokens with local/open
  models than plain Markdown/YAML → **plain Markdown, always** for a local-model setup `[a3]`.

## 8. Local/sovereign stack picks (all Apache/MIT, no cloud key) `[a8]`

- **Tier 2 (A):** `ripgrep` (zero-ops) → `SQLite FTS5` (BM25, single file, stdlib). No GPU/server.
- **Tier 4 (optional B), embedded:** `sqlite-vec` or `LanceDB` (in-process, no daemon). *Avoid*
  `pgvector` (needs a live Postgres server) for a minimal-ops solo setup.
- **Local embedder (single consumer GPU):** `Qwen3-Embedding-0.6B` (Apache-2.0, MTEB-leading small) or `BGE-M3`
  (one model → dense+sparse+ColBERT, enabling local hybrid without a second call).
- **Reranker:** `bge-reranker-v2-m3` (Apache-2.0, 0.6B, offline).
- **Flags:** `EmbeddingGemma` carries the Gemma license (usage terms, not pure Apache); Obsidian
  `Smart Connections` is source-available (no-compete clause) — both are *local* but not fully
  code-free, worth noting for a strict "sovereign" bar.

## 9. Contradictions & caveats surfaced (honesty log)

- **Vendor benchmarks flip by author** — Mem0's blog: 92.5%/94.4% and it wins; third-party
  vectorize.io: Mem0 49.0% vs Zep 63.8%, opposite ranking. All memory-framework numbers are
  **directional only** `[a1]`.
- **"Everyone dropped embeddings" is partly secondary-sourced** — the Boris Cherny / May-2025 removal
  claim traces to an HN/talk paraphrase, not a primary Anthropic post; the "Amazon Science >90%" claim
  is uncited. The *primary-sourced* facts (Cursor's own numbers, GrepRAG paper, Aider repo-map,
  Anthropic's blueprint) are enough to carry the conclusion without them `[a4]`.
- **The "150-line / 20-23% cost" AGENTS.md statistic is blog-only** — no primary study; do not cite as
  fact (the ~150–200 instruction cliff is separately corroborated by Anthropic's own "bloated CLAUDE.md
  → ignores instructions" language) `[a2]`.
- **Not verified**: local-footprint (VRAM/latency) numbers for the embedders at query time at your
  own scale; llama.cpp-native reranker serving path `[a6,a8]`.

## 10. Open questions for the maintainer
1. **Scope of "everything":** just the agent's *operating* knowledge (rules/decisions/history), or
   also large *content* corpora (generated build samples, a large content archive, a large document
   estate)? The first = pure A; the second = a dedicated retrieval pipeline's B design. They are
   different tools for different jobs — the answer sets how much of Tier 4 you ever build.
2. **Cross-project or per-project?** Recommend one **global** enforcement + wiki *standard* (a skill/
   template), instantiated per project — not a monorepo.
3. **Build the enforcement hook now?** It's the highest-ROI, lowest-cost, and directly fixes the
   complaint that started this. Say the word and it's a small, testable change.

_Sources: `corpus/agent-01..10-*.md` (verbatim agent reports) + `PROCESS.md` (methodology)._

## 11. Design rationale + measurement comparability

Separate commission: fixing a wiki where rationale is buried in chronological logs, benchmark
numbers across several files aren't comparable, and names are ambiguous. Full sourcing in
`corpus/agent-11-design-rationale-and-measurement.md`.

**Already-solved, adopt by name:**
- **ADR (Nygard) / MADR**, for "why does it work this way" — Title/Context/Decision/Status/
  Consequences, and the load-bearing rule: **never edit an accepted ADR, only supersede it**, so the
  log of what governed the work when stays intact `[a11]`.
- **Diátaxis's "explanation" mode**, kept as its own document type, never blended into how-to/
  reference — matches this corpus's own §7 finding (`grep tax`, verbose-plain markdown) that mixing
  content types degrades a plain-markdown wiki `[a11,a3]`.
- **arc42 §9** pattern: one dedicated, central "decisions" section (or per-decision files), explicit
  judgment call on central-vs-local placement, cross-referenced rather than duplicated `[a11]`.
- **MLflow/DVC's run model**: a run = params + metrics + tags + artifacts, with the pipeline/schema
  version itself logged as a tracked param (DVC's `dvc.lock`, MLflow tags) — this is the direct fix
  for "several files, not comparable, because the pipeline changed between runs" `[a11]`.
- **Backstage's typed, namespaced entity reference** (`kind:namespace/name`) and DNS's canonical-
  name-plus-aliases (RFC 1034) — the fix for "the pipeline means six different things": give each
  sense a qualified canonical name, treat bare mentions as aliases that resolve to one `[a11]`.
- **AutoResearch's negative-knowledge record** (`task_id / attempted_route / observation / failure /
  rationale / recommended_alternative`) as the shape for a "tried and failed" registry — structured,
  not prose, and meant to be re-injected into the next attempt rather than filed away `[a11]`.

**Genuinely ours to invent — no prior art found:**
- **No named pattern exists for "these two numbers came from different pipelines, do not compare
  them."** The mechanism is solved (pin pipeline/schema version as a run attribute, group by it) but
  no source names the failure-to-avoid itself — we have to define and label that convention
  ourselves `[a11]`.
- **No literature names the "one word means six things" disambiguation problem** as its own pattern
  — only the generic qualify-by-namespace mechanism. The DDD "bounded context" idea is a plausible
  fit but was **not verified this pass** — flagged as unfetched hypothesis, not a citable finding
  `[a11]`.
- **What makes a negative-results registry actually get read** has no single sourced answer — two
  separate literatures converge (remove the cost of admitting failure; make records structured and
  auto-surfaced to the next attempt, not browsed) but neither source states it as one finding — this
  agent's synthesis, not a direct citation `[a11]`.
- **C4 explicitly has no rationale artifact** (confirmed by direct fetch of its FAQ) — don't expect
  to borrow a "why" layer from it; pair a structure notation like C4 with Diátaxis explanation + ADR.

**Weakest link — RESOLVED.** Horner & Atwood could not be fetched by the lane at first (PDF
undecodable, proxy 503'd); it was later obtained and read in full. It is **"Design Rationale: The
Rationale and the Barriers," NordiCHI 2006, pp. 341-350** — settling the lane's two-similar-titles
question. Verbatim quote table in lane a11 §Q2 RESOLVED.
Every unconfirmed framing is confirmed: five barrier categories (cognitive/capture/retrieval/usage/
**organizational**), the structure-vs-capture-effort trade-off, the gulf-of-evaluation problem, and
— the one that matters most for any agent-facing knowledge design — **"designers cannot recognize
the relevance of rationale until a person queries it … later uses may not be able to specify what
information will be most useful, but rather will only recognize that they do not have the necessary
knowledge"** (§Retrieval → Relevance). That is the search-cannot-serve-you case, sourced `[a11]`.

**It also contradicts a common design instinct, and the contradiction is load-bearing:**
*"We do not want to force the content to be too structured but need to provide structuring
mechanisms so that it can be automatically structured or restructured at a later time"*
(§Organizational Limitations). A fixed schema imposed on the **author at write time** is the
documented failure mode; the schema must be applied **after** capture, by a mechanism that is not
the person with the idea. Paired with Grudin's rule quoted there — *"benefits to the current users,
not just the future users"* — this is the strongest practical constraint the literature places on a
wiki/ADR design `[a11]`.


---

## 12. The design that came out of this research

`DESIGN.md` in this folder is the **portable** form of the wiki rebuilt on one project using
lanes a1-a11: the load classes and their caps, the ten-line generated-overview header, ADR bodies with
supersession, the always-loaded map of dead ends, rig-keyed measurement ledgers with `RIG-BREAK`,
scripts-as-interfaces, point-at-executable-facts, capture-free-form-structure-later, and what
deliberately is NOT built with the threshold that would change it.

A worked example with real byte counts and the migration phases guided these choices; it stayed with
the source project and is not shipped here. **Intended for reuse on any entity-rich project** whose
existing wiki already follows Option A.
