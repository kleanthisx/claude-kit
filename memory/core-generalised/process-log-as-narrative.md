---
name: process-log-as-narrative
description: "The user wants the WORK PROCESS logged as a chronological narrative (idea → options → what was checked → results → decision → test → landing, tables included) into the project's ACTION-LOG.md — not a findings summary. The 'write it myself, no scribe subagent' half is FABLE-ONLY: Fable's guard cuts the scribe over the phrase 'thought process'. On every other model use the standing scribe (user, 2026-09-12; scoped 2026-09-13)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c70b1007-9573-41fe-8972-5240b6dc2ff7
  modified: 2026-09-13T06:42:07.588Z
---

> **AMENDED 2026-09-16 — the Fable-only carve-out is now universal.** There is no scribe on any
> model; `/wrap` step 7 governs: "the wiki is written by the assistant, never by a scribe subagent."
> Ground truth is the rendered transcript (`wiki/render_session.py`). See [[scribe-agent-records-everything]].


User (2026-09-12, a chat webapp register work): "what i asked from the scribe is to also log the work process
along the way, not only findings. if we read their file is like someone sitting here with us. 'we came up with
this idea and explored these options.. did search, got these results back, decided on this, run this tests,
landed here..' and so forth. tables and all. so next time we ask 'what the hell is this default do? where it came
from? and why is it structured this way?' we can trace it back." Then: "stop using scribe."

**Why:** decisions made between tool calls (options weighed, rejected alternatives, why a value is what it is)
vanish unless narrated at the time; a findings-only log answers "what" but not "why this shape". It is the user's
own work process being documented, not a record of Claude.

**How to apply:** in `an RP project/docs/wiki/ACTION-LOG.md` (and the equivalent file in other projects), write at each
decision point — not at the end — a paragraph in "we" voice: the idea, the options on the table and why each was
dropped, what was checked and what came back (numbers in tables), the decision, the test, where it landed, with
the files touched.

**Who writes it — model-dependent (user, 2026-09-13):** the "no scribe subagent" clause applies **only when
running on Fable**. Fable is monitored strictly against thought-process distillation, and because the log is
described as recording the *thought/work process*, that guard cuts the scribe — it reads the request as an attempt
to log Fable's own internal reasoning, which is not what is wanted. The user's words: "its illogical to block the
logging of my thought and work process, but somehow it thinks i want to log the internal thought process of
fable". On Fable: write ACTION-LOG.md myself, inline, no scribe. On every other model (Opus/Sonnet/Haiku): keep
the standing scribe subagent per [[scribe-agent-records-everything]] and feed it at each decision point.
What never changes is the *content* — the chronological narrative. Related:
[[log-experiments-not-just-conclusions]], [[one-change-per-run-subtract-to-find-fault]],
[[scribe-logs-process-not-just-findings]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
