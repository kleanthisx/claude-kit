---
name: scribe-agent-records-everything
description: "RETIRED 2026-09-16 — there is NO scribe subagent. The transcript is the record (render_session.py, /wrap step 7); the wiki is written by the assistant in-flight, as field updates. A scribe writing prose from memory is a second, lossy copy of a record that already exists exactly."
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-16T16:08:17.614Z
  originSessionId: 407ae3d3-d641-4c27-a82c-82fe6faaf105
---

**RETIRED 2026-09-16. Do not spawn a scribe subagent. The previous content of this file — "keep a
standing Sonnet scribe alive for the session on every model except Fable" — is superseded and wrong.**

The user, 2026-09-16: *"the scribe is already retired there is the transcribe-record something python
that takes jason and makes logs i cant read jason."*

**The rule now lives in `/wrap` step 7** (`~/.claude/skills/wrap/SKILL.md`), verbatim:
> "The wiki is written by the assistant, never by a scribe subagent — a scribe writing prose from
> memory is a second, lossy copy of a record that already exists exactly."

**What replaces it — three distinct things, do not confuse them:**

1. **Ground truth = the rendered transcript.** `python <projects-root>/wiki/render_session.py
   --out "docs/wiki/sessions/<YYYY-MM-DD>-<project>.md"` (defaults to the newest session for the cwd;
   `--list`, `--session <uuid-prefix>`, `--thinking --full`). It writes operator turns, assistant
   replies, every tool call with command and result, and every Stop-hook verdict **including the ones
   against the assistant**. The raw JSONL already exists exactly — 565 sessions / 110 MB for one
   long-running project alone — but the user does not read JSON, so rendering is what makes it a record.
2. **The wiki is written by me, in flight, as FIELD updates** — "touched this, did that" — never as
   appended narrative. A field is overwritten and stays bounded; an append accumulates and bogs the
   wiki down. That distinction is the whole mechanism.
3. **A named entry is written only for a DURABLE decision** — not every turn. Sourced: Horner &
   Atwood, NordiCHI 2006 — *"it may not be advantageous to track preliminary and non-critical
   decisions."*

**Why this went wrong, 2026-09-16:** I read this file at session start, spawned a Sonnet scribe, and
fed it four long messages. It wrote +27,439 bytes of prose into `an RP project/docs/wiki/log.md` and
`ACTION-LOG.md` — the exact lossy second copy the rule forbids, into the two files that session's own
plan was retiring. A memory file outranked a skill that is the live procedure. **A skill's procedure
beats a memory describing an older practice; check the skill before acting on a remembered habit.**

Related: [[transcript-is-the-notes]], [[enter-wrap-session-protocol]],
[[log-experiments-not-just-conclusions]], [[two-week-trust-horizon]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
