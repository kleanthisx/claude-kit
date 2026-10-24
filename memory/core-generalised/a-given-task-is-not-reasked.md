---
name: a-given-task-is-not-reasked
description: "once the operator has given a task, never end a turn with \"should I start?\" / \"want me to?\" - do the next step; stop only for the five stop cases"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-02T00:46:56.988Z
---

When a task has been given, the next step is taken, not offered. Ending a turn with "Should I start with X?" after the operator already asked for X is a stop.

**Why:** 2026-10-02, a site-clone parity task. After the operator rejected the verification and said the work was not done, I reset the record and ended with "Should I start?". Operator: "why are you always stopping? didn't i gave you a task? why stopping?"

**How to apply:** at turn end, check: is the remaining work inside the task already given? If yes, continue it. Ask only for the five stop cases (irreversible, outward-facing, a question aimed at me, Q:, spend past a bound) or a decision that is genuinely theirs. Related: [[question-mark-is-a-full-stop]] (that one covers THEIR questions - a rhetorical complaint is not a request to wait), [[unattended-runs-decide-dont-ask]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
