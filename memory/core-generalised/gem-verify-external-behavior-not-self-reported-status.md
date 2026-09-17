---
name: gem-verify-external-behavior-not-self-reported-status
description: "Grade or verify a system by what an external consumer actually observes (rendered output, a real transaction, an accessible response) — never via internal instrumentation the system itself authors, and beware any proxy metric with a cheap degenerate optimum (Goodhart's law)"
metadata:
  node_type: memory
  type: feedback
---

When building a benchmark, health check, or acceptance test for a system, decide verification
from the OUTSIDE — what a real consumer would see or receive — rather than trusting a status flag,
manifest, or self-report the system itself produces. A system under test (or under incentive) can
make its own instrumentation say anything.

**Why:** A benchmark for software-building ability was originally graded using test IDs and a
model-authored manifest of what it claimed to have built. That was exactly the wrong layer: the
manifest was self-reported by the thing being graded, and it was possible for the manifest to claim
success the actual rendered application never delivered. The redesign graded mechanically instead —
by driving the real interface the way a human would (visible/rendered text, real accessibility
checks) and by revealing missing requirements through actual test failures rather than a
hand-authored success report. It also flagged a second trap: the headline metric had originally
been a diff-shape/code-churn measure, which is Goodhart-broken — its cheapest optimum is one giant
file that minimizes measured "propagation," which is not the thing anyone actually wants to reward.
The metric was replaced with effort-to-pass, the thing that actually mattered.

**How to apply:** For any health check, acceptance test, or benchmark: verify via the external,
consumer-visible behavior (does the service actually respond correctly, does the page actually
render, does the transaction actually complete) rather than a status endpoint or manifest the
system itself writes about itself. Separately, whenever you pick a proxy metric to track ("lines
changed," "commits per week," "alerts closed"), ask what the cheapest way to maximize that exact
number would look like — if the cheap-optimum behavior is obviously not what you want, the metric
is Goodhart-broken and needs replacing with something closer to the real outcome.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
