---
name: scribe-logs-process-not-just-findings
description: "The log (scribe-written, or written by me on Fable) must record the WORK PROCESS as a chronological narrative — idea, options weighed and dropped, what was checked and what came back, decision, test, landing — not just findings; written at each decision point, not summarized at the end (user, 2026-09-12)"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-13T06:42:27.614Z
  originSessionId: e13cd0c7-a27e-454e-a43f-39d75c4e7936
---

The content requirement, independent of who writes it: one narrative unit per **decision point**, in "we" voice —
the idea, the options that were on the table and why each was dropped, what was checked and what came back
(numbers in tables), the decision, the test that was run, where it landed, and the files touched.

**Why:** a findings-only log answers "what" but not "why this shape". The reasoning between tool calls — rejected
alternatives, why a default holds the value it holds — exists nowhere else and is gone at compaction. It is the
**user's** work process being documented, not a record of Claude's internals.

**How to apply:** write it as the work happens, not as a summary at the end. Who holds the pen is model-dependent:
on Fable, me directly (its guard cuts the scribe — see [[process-log-as-narrative]]); on every other model, the
standing scribe subagent, fed one message per decision point (see [[scribe-agent-records-everything]]). Related:
[[log-experiments-not-just-conclusions]], [[one-change-per-run-subtract-to-find-fault]].
