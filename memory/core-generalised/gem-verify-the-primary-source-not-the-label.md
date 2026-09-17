---
name: gem-verify-the-primary-source-not-the-label
description: "A product/component's marketing name or label is a CLAIM about its method, not a verified property — check the primary technical documentation before trusting the label, and never compare two things across an uncontrolled confounding variable while attributing the difference to the variable you meant to test"
metadata:
  node_type: memory
  type: feedback
---

A name like "unlocked," "hardened," "enterprise-grade," or "uncensored" describes an intended
outcome, not a verified mechanism. Before relying on it, read the primary source (the vendor's own
technical documentation, a changelog, a build manifest) for what was actually done and what its
own documented limitations are.

**Why:** Comparing several local models by an "uncensored" label produced a confusing result: one
model behaved oddly and it was attributed to an unrelated cause (quantization/cache artifacts).
Checking each model's own technical registry entry showed the real story — one model in the
comparison hadn't been modified at all (an official, fully-aligned build), a second used a partial
technique whose own documentation explicitly named the exact artifact being misdiagnosed as
"instability," and a third used a well-documented, thorough technique with near-zero measured
refusals. The comparison had silently been measuring alignment status, not the quality axis it was
meant to measure, because the items being compared differed on an uncontrolled variable the person
running the comparison hadn't checked.

**How to apply:** Before trusting any label that claims a method was applied (patched, hardened,
sanitized, uncensored, GDPR-compliant), pull the primary source — the actual changelog, config, or
technical card — and record what method was used and what its own documented failure modes are.
Before comparing two systems on any axis, verify they are not ALSO differing on some other,
unstated axis (one has debug logging on, one is running an older patch, one was rebooted more
recently) — a comparison that doesn't control for a confound measures the confound, not the thing
you think you're testing.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
