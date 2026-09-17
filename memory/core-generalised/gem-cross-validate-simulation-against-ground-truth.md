---
name: gem-cross-validate-simulation-against-ground-truth
description: "Before trusting a simulated/modeled pipeline's numbers, validate a sample of it against an independent, real-world execution engine — and fix the stop-criterion/kill-switch threshold BEFORE going live, not after"
metadata:
  node_type: memory
  type: feedback
---

A simulation or historical-replay model that has never been checked against an independent
real-world engine is a hypothesis, not a validated result — however internally consistent its own
numbers look. Before relying on it for a real decision, run a subset through the real, independent
path and compare.

**Why:** A financial-strategy simulation pipeline produced its own performance numbers for a set of
candidate strategies from historical market data. Before trusting those numbers to commit real
capital, a sample of the strongest candidates was independently re-run through a separate, real
execution engine on the identical historical data. The two engines' trade counts agreed within
2-6%, with no systematic bias in either direction — only after that independent cross-check did the
pipeline's numbers become trustworthy enough to act on. Separately, before any of it went live, an
explicit stop-criterion was agreed in advance (a rolling performance threshold below which further
commitment stops) rather than left to be decided under pressure later, once real money was already
on the line.

**How to apply:** Whenever a modeled/simulated result is about to drive a real decision — a
capacity-planning model, a synthetic monitoring probe meant to stand in for real user traffic, a
staged rollback plan — run a sample of it through the real, independent path first and check the
numbers agree within a stated tolerance before trusting the model for anything consequential.
Separately, decide the objective threshold at which the system stops or escalates BEFORE it goes
live, in writing, so that decision doesn't have to be made under the pressure of an already-bad
situation.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
