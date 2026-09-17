---
name: gem-hard-crisis-floor-plus-exclude-discredited-methods
description: "Any advisory/triage system needs a non-negotiable escalation floor for the worst-case that overrides normal routing, PLUS an explicit exclusion list of discredited methods — a generic 'evidence-ranked' default is not enough on its own"
metadata:
  node_type: memory
  type: feedback
---

When designing a system that routes a case to one of several methods based on the situation
(a triage system, an advisory tool, an alerting pipeline), two things must sit outside the normal
routing logic, not inside it: (1) a hard floor that fires on the worst-case regardless of what the
normal routing would have chosen, and (2) an explicit list of methods excluded by name because
they are discredited, not merely down-ranked by the general scoring.

**Why:** Designing an advisory persona (2026-07-13) meant choosing among several well-established
methods case by case, evidence-ranked by the kind of problem presented. That routing logic alone
was not sufficient: the design also needed a hard, always-on crisis floor (specific emergency
contacts, unconditionally surfaced) that the normal method-routing could never suppress, and a
named exclusion of certain popular but discredited techniques that a generic "pick what the
evidence favors" ranking would not reliably filter out on its own, since a bad method can still
score plausibly against the wrong metric.

**How to apply:** In any system that triages or routes toward an action — a monitoring pipeline
choosing which alert handler to invoke, a runbook selecting a remediation path — do not rely on
the general scoring/ranking to also catch the worst case or to filter out known-bad approaches.
Write both as separate, unconditional rules: a floor condition that always escalates regardless of
what else fires, and a named denylist of approaches excluded outright rather than left to be
outscored. Verify periodically that the floor condition still fires under a live test, since an
untested escalation path is not a working one.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
