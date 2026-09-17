---
name: enter
description: The standard way to ENTER/orient to a project before doing any work. Use when the user says "/enter", "enter <project>", "let's move into <project>", "open <project>", "get me oriented", "what's the state of this project", or whenever starting fresh work in a project you have not yet oriented to this session. Read-only: it reads the project's entry ledger + the files it points to, checks git, reports the lay of the land, then stops and waits — it never starts building.
tools: Read, Glob, Grep, Bash
---

# /enter — unified project init

Orient to a project the same way in every project, then hand back to the user. **This is read-only. Do not edit, create, or run anything that changes state. Do not start the task — report and stop.**

The counterpart is `/wrap` (shutdown). Enter reads what wrap wrote.

## Procedure

### 1. Find the project root
The root is the nearest directory (the cwd or an ancestor) that contains any of: `docs/wiki/`, `CLAUDE.md`, `AGENTS.md`, `PLAN.md`, or `.git`. If this machine runs a multi-project workspace (several projects under one root — see "Conventions" below) and the user named a project, use `<workspace-root>/<name>/`. If the cwd is the bare workspace root (no single project), ask which project in one line — do not guess.

### 2. Read the entry ledger — branch on which wiki this is

```bash
ls docs/wiki/entities 2>/dev/null && echo V2 || echo V1
```

**If `docs/wiki/entities/` exists → wiki v2.**

1. **Regenerate first.** `python docs/wiki/generate.py` — the four surfaces are **generated and
   gitignored**, so on a fresh clone they do not exist at all until this runs. Report its entity
   count, errors and warnings; errors mean the wiki is broken, not that you should proceed.
2. **You may already have them.** `<CLAUDE_HOME>/hooks/load-wiki.ps1` injects `OVERVIEW.md`,
   `DISCARDED.md`, `NAMES.md`, `DECISIONS.md` and `doctrine/` at SessionStart and after every
   compaction, if that hook is installed. If that injection is in context, **do not re-read those
   files** — say so and move on.
3. **Read `docs/wiki/TASKS.md`** — it is the next-session pointer in v2. `NEXT.md` is a redirect stub.
4. **Do not read `docs/history/`.** Ever, at orientation. It is the frozen record, cited by path from
   entity bodies when a specific claim needs checking.

Then resolve the user's words against `NAMES.md` before doing anything: a row marked **AMBIGUOUS
means ask**, not guess.

**Otherwise → v1.** Read the **first that exists**, in this priority:
1. `docs/wiki/decisions.md` **+** `docs/wiki/index.md`  ← the standard (see the hub's `WIKI-STANDARD.md` if this workspace has one)
2. `CLAUDE.md` / `AGENTS.md`
3. `PLAN.md`
4. `README.md`

Also read a next-session pointer if present: `docs/wiki/NEXT.md` (or a "Start here next" block in `decisions.md`) — `/wrap` leaves this for you.

### 3. Follow the pointed files
Read **only** the deep files the ledger explicitly names (specs, run docs, sub-project CLAUDE.md). Do not read the whole tree — the ledger points; you follow the pointers.

**In v2 the pointer is the entity.** Resolve the thing you are about to touch to `kind:namespace/name`, then read that one entity file whole — header, decisions, discards, invariants. `guard-entity-read.ps1` will block an edit to a file whose owning entity you have not read, so this is not optional anyway.

### 4. Check git + freshness
```bash
git status -s            # dirty/uncommitted work
git log --oneline -8     # recent history
```
Also note the most-recently-modified source files (they signal the live thread). If not a git repo, say so.

### 5. Report the orientation, then STOP
A compact report the user can skim — no building:
- **What it is** — one or two lines.
- **Current state** — what's done / where the plan sits (cite the ledger line).
- **In-flight / uncommitted** — dirty-git summary (file count, rough diffstat); flag it plainly if large.
- **Open threads / start-here** — from the next-session pointer.
- **How to run it** — the project's own serve/launch script (prefer it over reconstructing commands).
- End with: which thread are we in? — and wait.

## Conventions (carry these in)
- **If this machine runs a multi-project workspace** (a `projects/`-style tree with a shared hub wiki, commonly `<workspace-root>/wiki/`): before invoking or recommending any shared local model or asset, check the hub's registry — never from memory.
- **Hub-and-spoke:** generic facts live in the hub wiki; project facts live in `<project>/docs/wiki/` (spoke). Link, never copy.
- **No hub wiki found** above this project (a single-project install, or entered outside a multi-project workspace) → skip the hub references and just use the local ledger fallback described above.
- Report as evidence: "ran `<cmd>` → `<output>`". Do not fabricate state — read it.
