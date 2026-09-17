# Wiki Standard — the unified convention for every project wiki

> One convention, applied to the **hub** (a top-level `wiki/` shared across projects) and to
> **every** project spoke (`<project>/docs/wiki/`). Promoted from a working project's own
> "Knowledge wiki" convention (which shipped real work) and generalized to every project in a
> workspace. Grounded in sourced research: see `wiki-v2/SYNTHESIS.md` in this kit.

## The model: LLM-maintained plain-markdown wiki (Karpathy pattern), NOT a vector DB

Knowledge is a maintained **markdown** wiki in **git** — plain text the model reads/greps/writes
directly. No embeddings, no vector store. This is the research-backed default for a solo dev with
large-context local models: every major coding agent loads plain markdown wholesale at startup, and
a curated corpus stays grep-navigable to ~hundreds of pages before a vector index earns its place.
See `wiki-v2/SYNTHESIS.md` for the evidence and the thresholds where you'd add one.

## Hub-and-spoke (the anti-duplication rule)

- **Single source of truth.** Every fact lives in exactly ONE place.
- Fact true for **≥2 projects** → the **hub** (top-level `wiki/`).
- Fact true for **exactly 1 project** → that project's **spoke** (`<project>/docs/wiki/`).
- Spokes **link up** to hub pages with a relative/absolute link; they **never copy** the content.
  When you catch yourself re-explaining a shared service, a shared asset, or shared tuning inside a
  project wiki — stop, put it in the hub, and link.

## Page conventions

- **Naming:** `<category>-<topic>.md` (e.g. `infra-monitoring-agents.md`). One category per page.
- **Categories:** `infra` (hosts/services/hardware/deployment) · `knowledge` (domain theory) ·
  `pipeline` (build agents/prompts/automation) · `tooling` (agentic flow, MCP, launchers) · `design`
  (project-specific specs). Projects may add their own, documented in their spoke `index.md`.
- **`index.md`** — the front door / catalog. Every project wiki has one. Add every new page to it.
- **`decisions.md`** — the tried/proven/discarded ledger; the ONE page read on startup (compact by
  design). One line per durable decision: `**name** — STATUS — what/why. [src]`
  (PROVEN ✓ · DISCARDED ✗ · STANDING ⚖ · OPEN ?). Add a line whenever a durable decision is made.
- **`log.md`** — append-only, newest on top. `## [YYYY-MM-DD] <category> | <headline>`. **Log
  dead-ends too** — a rejected approach is as valuable as a win.
- **Cross-link** with relative links `[topic](category-topic.md)`; hub links use the full path or a
  relative `../../wiki/…`.
- **Raw history** (`sessions/`, `transcripts/`) is on-demand only, **never preloaded**; distil it
  into category pages + `decisions.md`.

## Writing style (research-backed)

- **Plain Markdown, verbose natural language.** NOT dense symbolic/compressed notation — the
  "Index Sickness" study (391 sessions) found compressed symbolic KBs drift into self-referential
  nonsense; cutting volume + switching to natural language fixed it. Also avoids the local-model
  "grep tax" (custom compact formats cost more tokens on open-weight models).
- **Keep the always-loaded surface small.** `decisions.md` + `index.md` are the in-context core;
  everything else is pulled on demand (grep/read). Bloat causes the model to *ignore* instructions
  (the ~150–200-instruction compliance cliff).
- **Provenance on every claim.** Source it (file, run output, URL + locator) or mark it unverified.
  A stale "fact" stated with confidence is worse than an admitted gap.

## Maintenance workflows

- **Ingest** — read a raw source → write/update the page(s) → update `index.md` → append `log.md`.
- **Query** — grep the pages, synthesize with citations; a keeper answer becomes a page.
- **Lint** (periodic) — health-check for contradictions, stale claims, orphan pages, broken links,
  human-edits silently reverted. This is the named mitigation for wiki drift; run it before trusting
  the wiki after a big change.
- **Promotion habit** — the moment a durable process/infra/tooling decision is made, write it to a
  page **+** a `log.md` line **+** a `decisions.md` line. Promotion is the missing step that lets
  rejected ideas resurface next session.

## Currency (why this doesn't rot)

The failure that motivated this standard: sessions referencing **deleted/abandoned resources**
(a removed host, a decommissioned service, a model no longer on disk) as if they were still live.
Two guards:
1. **Structured facts get a verifier.** A registry of concrete things (models, hosts, services,
   scheduled jobs — anything with a lifecycle) should carry status + last-verified columns, and pair
   with a small script that diffs the table against reality (disk, `systemctl`, an API, whatever the
   registry describes). Prose can't validate itself; scripts can. Test any such check against
   something known-absent before trusting it — a check that cannot fail is not a check.
2. **Enforcement, not persuasion.** The reliable fix for "the agent didn't read the wiki" is a hook
   that re-injects the compact rule-set / `decisions.md` at **session-start and after every
   compaction** — because injected files are otherwise framed as advisory and dropped on compaction.
   See `wiki-v2/SYNTHESIS.md` §1. (`~/.claude/hooks/` is where this lives.)
