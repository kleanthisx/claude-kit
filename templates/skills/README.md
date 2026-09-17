# Adapting the skills at a new site

`skills/enter` and `skills/wrap` are written to work unmodified on day one — they degrade
gracefully when the things they check for do not exist. This page says what to look at anyway, and
what the optional pieces they reference actually are, so a session at the new site can set them up
deliberately instead of by accident.

## What works with zero setup

Both skills fall back to a **single-project ledger** (`docs/wiki/decisions.md` + `index.md`, or
`CLAUDE.md`/`AGENTS.md`/`PLAN.md`/`README.md`, whichever exists) and skip every hub/workspace
reference when the things they point at are not on disk. A brand-new site with one repo and no hub
wiki gets a working `/enter` and `/wrap` immediately.

## What to adapt if this site runs MULTIPLE projects under one root

If the site has a `projects/`-style tree (several independent repos under one parent directory,
each with its own git history), decide early whether you want the cross-project layer:

1. **Fill in `templates/doctrine/CLAUDE.workspace.template.md`** — replace `<WORKSPACE_ROOT>`,
   `<HUB_WIKI>`, `<ASSET_REGISTRY>` and `<OPS_BOARD>` with real paths, delete the template notice at
   the top, and drop the result at the workspace root as its own `CLAUDE.md`.
2. **Stand up the hub wiki** at whatever path you named `<HUB_WIKI>` — at minimum an `index.md` and
   a `WIKI-STANDARD.md` describing the ledger convention your projects will follow. `enter`/`wrap`
   both read `WIKI-STANDARD.md` by reference, never by copying its rules — keep the convention
   there, not duplicated into the skill.
3. **Name your `<ASSET_REGISTRY>`.** The source design used this for a local-model registry
   (ACTIVE/PROTECTED/DEPRECATED/DELETED). At a sysadmin/ops site this is more likely a device
   inventory, credential/asset registry, or a list of monitored hosts — same shape (a single file
   that says what's current so nobody references something that was decommissioned), different
   domain. `enter` checks it before recommending anything shared; `wrap` doesn't touch it.
4. **Decide on a ticket board.** If jobs get big enough to need budgeting (output-token caps,
   multi-agent fan-outs), fill in `templates/ops/OPS.template.md` and point `<OPS_BOARD>` at it.
   If not, skip it — `wrap` step 9 is a no-op without one.

## What to adapt for the wiki layout itself

`enter`/`wrap` support two per-project wiki layouts and auto-detect which one a project uses by
checking for `docs/wiki/entities/`:

- **v1** — `docs/wiki/decisions.md`, `index.md`, `log.md`, `NEXT.md`. Hand-maintained, append-only.
  No extra setup: this is the default a project falls into if it has any `docs/wiki/` at all.
- **v2** — `docs/wiki/entities/*.md` (one file per named thing, with an `owns:` header line) plus a
  `generate.py` that builds `OVERVIEW.md`/`DISCARDED.md`/`NAMES.md`/`DECISIONS.md`/`TASKS.md` from
  the entities. Requires more setup (the generator, the entity schema, the two hooks below) but
  scales better once a project accumulates enough history that a hand-written log stops being read.
  Do not migrate a project to v2 casually — it is a structural commitment, not a file rename.

If you adopt v2 for a project, also install (from `hooks/`):
- `hooks/load-wiki.ps1` — SessionStart/PostCompact injection of the generated surfaces. No-ops on a
  project without `docs/wiki/entities/`.
- `hooks/guard-entity-read.ps1` — blocks an edit to a file until the wiki entity that owns it has
  been read this session. Same no-op behavior on a v1 or wiki-less project.

## What NOT to do

- Don't hand-write `OVERVIEW.md`/`DECISIONS.md`/`DISCARDED.md`/`NAMES.md` in a v2 project — they are
  generated; `wrap`'s own guardrail says so.
- Don't copy the hub wiki's content into a project's spoke wiki "for convenience" — link to it. The
  hub-and-spoke rule exists so a fact gets corrected once, not N times.
- Don't invent a ticket board or asset registry you don't intend to keep current — an unmaintained
  registry is worse than none, because `enter` will cite it as ground truth.
