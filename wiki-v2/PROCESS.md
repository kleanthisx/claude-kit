# Agent Operating-Memory: Wiki vs KB-Retrieval — Research Process

> **What this is.** A documented, sourced research effort on *how a solo developer should formalize
> the way an AI coding agent bootstraps and retrieves its OPERATING KNOWLEDGE* — the agent's rules
> (CLAUDE.md/AGENTS.md), project history & decisions, and long-term memory — so a fresh session
> reliably **loads and USES** the right context. The explicit fork under study:
> **(A) a curated LLM-maintained markdown "wiki" + text/grep search** (Karpathy LLM-wiki pattern,
> what an existing project wiki already does) vs **(B) a vector/RAG knowledge-base retrieval
> pipeline** (what a separate retrieval-research project explores) — or a hybrid.
>
> Commissioned by the maintainer. Directive: *"document the process and the findings — we don't
> want to say we did this but can't back it up."* This file is the audit trail. Raw agent outputs
> are preserved verbatim in `corpus/`. The recommendation lives in `SYNTHESIS.md`.

## The question (before any fetching)

**Decision to inform:** Given a solo maintainer, **local/sovereign** operation (no mandatory cloud
APIs), **large-context local models** already in the fleet (~256k context), and a **git-based**
workflow — should the agent's operating-knowledge system be a curated markdown wiki (A), a
vector/RAG store (B), or a hybrid, and *what mechanism actually makes the agent obey it*?

**Why this came up:** the observation that a fresh session "seems to not be able to read
CLAUDE and history or memory files." So the target is not just *storage* but *reliable load + use*.

**Prior art already on disk (read first, per the check-project-prior-art principle):**
- An existing project's `docs/wiki/` — a live **Karpathy LLM-wiki** (plain markdown + git + ripgrep
  search, no vector DB). Its `decisions.md` records that a vector knowledge-DB was **DISCARDED**
  once the big-context model could read curated pages directly — i.e. the constraint the vector DB
  solved went away.
- A separate retrieval-research project's SOTA survey — a cited 2025–2026 RAG landscape review. Core
  conclusion: *"there is no single best RAG"*; long-context **complements** rather than kills RAG;
  small static corpora can be stuffed/curated, large/dynamic need the pipeline; entity-completeness
  → graph.
- That same project's reasoning journal and model-tiering notes — model tiering, context handoff as
  text (not KV), MCP as the tool layer.
- Home operating memory: an instruction-decay finding and an enforcement-approaches finding
  (omission constraints decay over a session; deterministic hooks/gates enforce far better than
  prose; re-injection fixes compaction loss).

## Method (the six research rules, applied)

1. **Numbered question list before fetching** — the 10 lanes below.
2. **Rows before prose** — every agent returned a `| claim | source URL | locator/quote | date |`
   table before any narrative.
3. **Source locator on every claim** — URL + section/quote; claims without one are omitted or flagged.
4. **Record negatives** — "searched X, found nothing" is a logged finding in every report.
5. **Termination agreed up front** — each agent bounded to ~5–8 quality fetches / ~12 min; stop and
   note a source after 2–3 failed tries (a read-through proxy allowed for pages that block direct fetch).
6. **Fetch, don't recall** — agents were told to cite fetched pages, never answer from training memory;
   recall labelled as hypothesis.

**Model tiering:** multiple mid-tier web-research agents (mechanical fetch/summarize); synthesis by
one higher-tier reasoning thread. **Bound stated to user before launch:** ~10 mid-tier web agents +
1 synthesis pass, no writes/builds during research.

## The 10 lanes (deliberately overlapping at the seams so repeats can surface)

| # | Lane | Agent focus |
|---|------|-------------|
| 1 | Agent memory systems | Mem0, Letta/MemGPT, Zep+Graphiti, LangMem, Cognee, 2026 entrants — what/how stored, retrieval, local-hostability, benchmarks (LoCoMo/LongMemEval) |
| 2 | Coding-agent context files | CLAUDE.md, AGENTS.md standard, Cursor rules, Cline Memory Bank, Copilot instructions, Codex, Windsurf, Aider — load model, size limits, staleness |
| 3 | LLM-wiki / context engineering | Karpathy gist, Anthropic/LangChain/RAGFlow "context engineering", note-taking-app-as-memory — strengths + failure modes of curated markdown, scale ceiling |
| 4 | Grep vs embeddings | Why Claude Code dropped embeddings for agentic grep; Cursor/Sourcegraph/Aider; benchmarks; the crossover corpus size |
| 5 | GraphRAG / KG memory | MS GraphRAG, LazyGraphRAG, Zep/Graphiti temporal KG, Cognee, wikilink backlinks; solo-dev cost; when a graph is worth it |
| 6 | RAG SOTA deltas 2026 | Newest embedding models, Contextual Retrieval, late-interaction, RAG-vs-long-context 2026 |
| 7 | Evaluation | RAGAS, LongMemEval, LoCoMo; how to test "retrieved AND obeyed the right rule"; minimum-viable local eval harness |
| 8 | Local/sovereign stacks | sqlite-vec, LanceDB, Chroma, Qdrant, pgvector, txtai; local embedders; BM25/RRF/rerankers; ripgrep/tantivy/FTS5/Meilisearch; note-taking-app read-side |
| 9 | Why agents ignore context files | context rot, lost-in-the-middle, instruction decay, compaction; re-injection, hooks/gates, JIT loading — the *mechanism* that makes an agent obey |
| 10 | End-to-end blueprints | Claude Agent SDK memory tool, LangGraph memory, Pydantic AI + MCP, Letta, open "second-brain-for-LLM" writeups — copyable build orders |

## Run log

- 10 research agents launched in parallel (one message). Corpus files written verbatim
  as each returned. See `corpus/agent-NN-*.md` for raw outputs and `CROSSCHECK.md`/`SYNTHESIS.md`
  for the distilled result.

### Completion + provenance status
| # | Lane | Status | Corpus file | Tool calls / tokens (as reported) |
|---|------|--------|-------------|-----------|
| 1 | Memory systems | done | `corpus/agent-01-memory-systems.md` | 16 / 50.8k |
| 2 | Coding-agent context files | done | `corpus/agent-02-coding-agent-context-files.md` | 21 / 81.7k |
| 3 | LLM-wiki / context engineering | done | `corpus/agent-03-llm-wiki-context-engineering.md` | 18 / 54.0k |
| 4 | Grep vs embeddings | done | `corpus/agent-04-grep-vs-embeddings.md` | 15 / 51.9k |
| 5 | GraphRAG / KG memory | done | `corpus/agent-05-graphrag-kg-memory.md` | 14 / 49.5k |
| 6 | RAG SOTA deltas 2026 | done | `corpus/agent-06-rag-sota-2026.md` | 16 / 51.4k |
| 7 | Evaluation | done | `corpus/agent-07-evaluation.md` | 18 / 54.0k |
| 8 | Local/sovereign stacks | done | `corpus/agent-08-local-sovereign-stacks.md` | 20 / 52.6k |
| 9 | Why agents ignore files | done | `corpus/agent-09-why-agents-ignore-files.md` | 20 / 57.2k |
| 10 | End-to-end blueprints | done | `corpus/agent-10-end-to-end-blueprints.md` | 12 / 62.0k |

**All 10 lanes complete.** Total subagent spend ≈ 565k tokens across ~170 tool calls.
Synthesis + recommendation: `SYNTHESIS.md`.

## Provenance caveats carried forward (do not lose these)
- **Vendor benchmarks are self-serving.** Memory-framework LoCoMo/LongMemEval numbers flip depending
  on who published them (Mem0's own blog: 92.5%/94.4% and it wins; a third-party benchmark site:
  Mem0 49.0% vs Zep 63.8%). Treat all as *directional*, verify on your own data before trusting.
- **Several key "everyone dropped embeddings" claims are secondary-sourced** (blog posts tracing
  back to an HN/talk remark), not a primary Anthropic engineering post. Flagged per-row.
- The "150-line AGENTS.md / 2,500-repo / 20-23% cost" statistic is blog-only, **no primary study
  located** — do not cite as fact.
