> **TEMPLATE — adapt at the site.** This is not installed as-is. It is the shape of a cross-project
> doctrine file for a multi-project workspace (a `projects/`-style tree holding several independent
> repos under one root). Fill in the placeholders (`<HUB_WIKI>`, `<ASSET_REGISTRY>`, `<OPS_BOARD>`,
> `<WORKSPACE_ROOT>`) for the target site, delete this notice, and drop the result at the workspace
> root as its own `CLAUDE.md` (it concatenates with the operator's home `~/CLAUDE.md` and each
> project's own `CLAUDE.md`). If the site is a single project, not a multi-project workspace, this
> file does not apply — skip it.

# Claude Code — workspace tree (cross-project layer)

This file auto-loads as an **ancestor** whenever a session launches from `<WORKSPACE_ROOT>` or any
project beneath it. It adds the **cross-project knowledge layer**; it does **not** replace the
operator's home `~/CLAUDE.md` (working agreement) or any project's own `CLAUDE.md`. All three
concatenate.

This is a **workspace of independent projects, not one codebase** — there is no root build / test /
lint, and this level is typically **not a git repo itself** (each project manages its own VCS).
To do real work, enter a project and read its own `CLAUDE.md` / wiki.

## The shared knowledge hub lives at `<HUB_WIKI>`

Generic knowledge that is true across projects is centralized there — **do not re-derive or
duplicate it**:
- ⭐ **`<HUB_WIKI>/<ASSET_REGISTRY>`** — the single source of truth for shared local models / devices
  / accounts / whatever this site's scarce shared assets are. Adapt the name to the domain: a
  sysadmin site might call this an asset registry or device inventory rather than a model registry.
- **`<HUB_WIKI>/project-map.md`** — what each project is + who calls whom.
- **`<HUB_WIKI>/WIKI-STANDARD.md`** — the convention every project wiki follows.
- **`<HUB_WIKI>/index.md`** — the hub front door.

## Tree-level entry points

No tree-level build / lint / test — real commands live inside each project. What you run *here*:
- **Session bookends:** `/enter <project>` (read-only orientation) then `/wrap` (checkpoint + ledger
  update) — the standard start/end of any work in this tree.
- **Registry currency:** if `<HUB_WIKI>` ships a verify script (mirroring
  `wiki/verify-model-registry.ps1` from the source design), run it before trusting the registry
  against what is actually on disk. Note which PowerShell binary is actually installed on this
  machine (`pwsh` vs Windows PowerShell) — do not assume.
- **Reference files at this level, if present:** `<OPS_BOARD>` (ticket board — see Tree-wide
  operations), plus any launch-notes / agent-fleet-notes files the site keeps.

## Two standing rules for this tree

1. **Registry currency — never reference a shared asset from memory.** Before invoking,
   recommending, or wiring any shared local model / device / credential, **check
   `<HUB_WIKI>/<ASSET_REGISTRY>`**. It should mark what's ACTIVE / PROTECTED / DEPRECATED / DELETED.
   If unsure it's current, run the hub's verify script if one exists (diffs the registry against
   disk). This rule exists because sessions kept pointing at deleted or abandoned things that only
   still lived in someone's memory.

2. **Single source of truth (hub-and-spoke).** A fact true for ≥2 projects lives in `<HUB_WIKI>`
   (the hub); a fact true for 1 project lives in that project's `docs/wiki/` (the spoke). Spokes
   **link up** to hub pages — they never copy. Caught re-explaining shared infrastructure or a
   shared asset inside a project? Move it to the hub and link.

## Tree-wide operations

- **`<OPS_BOARD>`** — the **ticket board + usage ledger**, if this site runs one. Every fan-out /
  heavy job is a ticket; budgets are **output** tokens; the main loop delegates execution to
  lower-tier agents. **At 80% usage: pause all ops** (if the reset is within the hour, may burn to
  ~95%). Log usage per run. See `templates/ops/OPS.template.md` for the ticket-board format.
- A usage-ledger / usage-tally file pair, if kept, are the live usage meters the 80% rule reads
  (statusline footer % paired with tally tokens at the same moment).

## On entering a project

- Read that project's `docs/wiki/decisions.md` (or `CLAUDE.md`/`AGENTS.md`) first if it exists — the
  read-on-startup ledger. Its wiki should conform to `<HUB_WIKI>/WIKI-STANDARD.md`.
- Prefer the project's own launch/serve script (e.g. `<project>/serve.ps1`) over reconstructing
  commands by hand.

_If this workspace's design basis is itself sourced from research (a wiki-vs-retrieval comparison,
an agent-memory study, etc.), cite it here the same way the source design does — by path, not by
re-explaining it._
