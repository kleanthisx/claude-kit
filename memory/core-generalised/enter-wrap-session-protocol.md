---
name: enter-wrap-session-protocol
description: Unified /enter (init) + /wrap (shutdown) Skills — the standard way to start and end work in ANY project under projects/
metadata: 
  node_type: memory
  type: project
  originSessionId: ae7d0b4e-723b-4898-9c4c-ad93a2b112ef
  modified: 2026-08-28T17:22:49.292Z
---

Two user-level Skills built 2026-08-28 give a **uniform enter/shutdown across every project**:
`~/.claude/skills/enter/SKILL.md` and `~/.claude/skills/wrap/SKILL.md`.

- **`/enter`** (read-only) — find project root → read the entry ledger in priority
  (`docs/wiki/decisions.md`+`index.md` → `CLAUDE.md`/`AGENTS.md` → `PLAN.md` → `README.md`) →
  read `docs/wiki/NEXT.md` pointer → follow pointed files → `git status`/`log` → report orientation
  → STOP. Never builds.
- **`/wrap`** (Full scope, chosen by user) — summarize changes → append `log.md` → update
  `decisions.md` if durable → write `docs/wiki/NEXT.md` → **propose** a commit (gated on an explicit
  yes, never auto-commit) → update `projects/usage-ledger.log`/OPS. Creates `docs/wiki/{index,decisions,log}.md`
  on demand if missing.

**Why:** codifies the cross-project wiki hub's WIKI-STANDARD conventions (decisions.md read-on-startup +
the promotion habit) into *callable* form so they stop decaying as prose — matches
[[enforcement-approaches-evidence]] (re-injection beats advisory prose).

**How to apply:** use `/enter` when moving into a project, `/wrap` when ending a session. Mechanism =
Skills (user chose skills over slash-commands/hooks, so they auto-trigger on matching intent).
**Rollout is on-demand:** each project gets its `docs/wiki/` ledger the first time `/wrap` runs there —
no big-bang pass. Skills register at session start, so they went live the session AFTER 2026-08-28.
Related: [[session-start-recite-directives]], [[check-project-prior-art]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
