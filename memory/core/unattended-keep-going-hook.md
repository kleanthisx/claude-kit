---
name: unattended-keep-going-hook
description: "Claude kept stopping after ~4 min in unattended runs, burning the 5h window idle; fixed by a Stop hook (keep-going.ps1) that blocks turn-end until a STOP-CASE line is given (2026-10-02)"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-01T22:32:43.238Z
---

User, 2026-10-02: *"it always stops. and i even say 'i will leave you unattended. proceed as you see fit.' still 4 minutes of work and then stop. 5 hour limits gone waiting."*

**Why:** a Claude Code turn ends whenever the model replies without a tool call; nothing re-starts it. A prose "proceed" loses to the many wait-triggers in the standing rules (≤6-item lists, pending-proposal, ask-on-silence, W-question "don't act"). Judge Dread (the only Stop hook) was mode=off, so nothing pushed either way.

**How to apply:** `~/.claude/hooks/keep-going.ps1` is wired as a second Stop hook (backup `settings.json.bak-2026-10-02-keepgoing`). It is a SETTING, not a phrase filter (user, 2026-10-02: "filtering everything for 3 words is a waste. make it a setting"): `/unattended on` writes `~/.claude/unattended.json`, `/unattended off` deletes it; the skill is operator-only (`disable-model-invocation`). No file = hook exits on one Test-Path. The first session to stop after arming claims the flag; other sessions ignore it. While armed it blocks the turn from ending unless the final message has a line `STOP-CASE: <reason>` (complete with evidence / irreversible / outward-facing / spend bound / operator-only decision parked in PENDING_APPROVAL.md). Cap 40 blocks per arming. In unattended mode: work the whole list, end only with a STOP-CASE line. Related: [[unattended-runs-decide-dont-ask]], [[unattended-defer-gated-ops]], [[enforcement-approaches-evidence]].
