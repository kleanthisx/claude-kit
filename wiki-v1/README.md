# Wiki v1 — hub-and-spoke

> Design and convention only. This folder ships **`WIKI-STANDARD.md`** — the rule set — not a
> scaffolded template. Build the actual hub and per-project spoke files directly from that
> standard's page conventions when you set up a site; don't wait for a generator.

## What it is

A **hub-and-spoke** knowledge layout for a workspace of several projects:

- A **hub** — one shared directory (e.g. a top-level `wiki/`) holding facts that are true across
  more than one project: a shared asset/resource registry, a project map, cross-project decisions
  and log, shared infrastructure notes.
- A **spoke** per project — `<project>/docs/wiki/`, holding only what's unique to that project.
  Spokes **link up** to the hub; they never copy hub content into themselves.

The single rule that keeps it from rotting into duplicated, drifting copies: **every fact lives in
exactly one place.** A fact true for ≥2 projects belongs in the hub. A fact true for exactly one
project belongs in that project's spoke. If you catch a spoke re-explaining something the hub
already owns, that's the signal to delete it from the spoke and link instead.

The wiki itself is plain Markdown in git, read and grepped directly by the model — no embeddings,
no vector store, at the scale this is meant for (see `WIKI-STANDARD.md` for the sourced reasoning
and the thresholds where that stops being true).

## When to pick v1

- **A handful of projects** (roughly single digits to a few dozen), each with a **small-to-medium**
  wiki (tens of pages, not hundreds of entities).
- You mainly need a **shared registry** of concrete things with a lifecycle — hosts, services,
  scheduled jobs, monitored endpoints, tools, credentials-by-reference — plus a project map and a
  compact decisions/log ledger.
- Reading the whole always-loaded surface (index + decisions ledger) costs a few tens of KB, not
  hundreds — i.e., a person could still read the hub `decisions.md` top to bottom without it feeling
  like a chore.

## When to pick v2 instead

Pick **`../wiki-v2/`** when a *single project's* wiki has become entity-rich enough that v1's flat
category pages stop being the bottleneck and the wiki itself becomes too expensive to read:

- Dozens-to-hundreds of distinct things (services, runbooks, checks, incidents, scripts) that each
  need their own reference page, not just a mention in a category page.
- The always-loaded surface (what everyone reads every session) has grown past what's comfortable —
  the v2 symptom is a project wiki that quietly became a 200+ KB "read everything" habit.
- You need **generated** overviews (so the summary can't drift from the source files), per-entity
  ownership for a read-before-edit enforcement gate, and rig-keyed measurement ledgers so numbers
  from different configurations don't get compared as if they were the same run.

v1's hub-and-spoke rule and its page conventions (`index.md`, `decisions.md`, `log.md`, naming,
writing style, currency/verification) still apply *inside* a v2 project's spoke position and at the
cross-project hub — v2 is a redesign of what goes **inside one project's** `docs/wiki/`, not a
replacement for the hub-and-spoke layer above it.

## Read next

- **`WIKI-STANDARD.md`** — the full v1 convention: page conventions, categories, `decisions.md` /
  `log.md` format, writing style, maintenance workflows, currency/verification.
- **`../wiki-v2/DESIGN.md`** — the v2 design, its thirteen load-class/header/ADR/ledger/enforcement
  choices, and when each one is worth adopting.
