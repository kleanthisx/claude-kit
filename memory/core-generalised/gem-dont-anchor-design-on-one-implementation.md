---
name: gem-dont-anchor-design-on-one-implementation
description: "When designing or researching a general layer that several things sit on, don't let ONE existing implementation's specifics become 'the yardstick' — it is a consumer and a data point, not the spec"
metadata:
  node_type: memory
  type: feedback
---

When the task is to design or investigate something at a general/shared level (a framework, a
standard, a category-wide runbook), and one concrete instance of it already exists, that instance
is prior art to cite — not the reference the general design should be measured against.

**Why:** Asked to research and design the shared state/memory layer underneath several
consumer applications, the analysis kept grounding itself in one specific consumer's existing
implementation details (its particular state table, its particular state machine) as if
that consumer's design choices defined what the general layer should look like. The user corrected
this directly: the existing implementation is an application OF the general framework, not the
framework itself, and treating it as the yardstick would bake one consumer's incidental choices
into what should be a general design.

**How to apply:** When asked to design or investigate at the level of a category (a general
runbook for "how we patch database servers," not "how we patched THIS database server"), explicitly
name any single existing instance as one example/consumer/data point in the writeup, and check
whether a design decision is justified by the general problem or is simply inherited from that one
instance's history. If a synthesis or design doc keeps citing the same one system for everything,
that is the signal to step back up a level before continuing.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
