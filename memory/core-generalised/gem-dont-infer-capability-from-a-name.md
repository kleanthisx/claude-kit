---
name: gem-dont-infer-capability-from-a-name
description: "A client that infers a capability (vision, protocol version, feature support) from a NAME or ID string will silently misclassify the moment the string doesn't match its expected pattern — declare capabilities explicitly instead"
metadata:
  node_type: memory
  type: feedback
---

When a client decides what a backend can do by pattern-matching the backend's name or ID string,
that inference breaks silently the moment the string is anything other than what the client's
author anticipated — and the failure looks like the feature simply doesn't work, not like a
misdetection.

**Why:** A coding-agent client auto-detected whether its backend supported vision purely from the
backend's model-name string. The backend was served under a fixed, cosmetic alias chosen for an
unrelated reason (so callers could connect regardless of which underlying model was actually
loaded), and that alias didn't match the client's expected naming pattern. The client silently
treated the connection as text-only and never sent images at all — even though the backend
genuinely supported vision. The fix was to stop relying on name-based inference and declare the
capability explicitly in the client's own config, and to keep that declaration in sync automatically
whenever the underlying backend changed.

**How to apply:** Whenever a system infers a capability, version, or feature flag from a string
(a hostname pattern, a model-id naming convention, a filename suffix used to guess a file type),
treat that as fragile by default. Prefer an explicit, out-of-band declaration of the capability
over pattern-matching a name — and if you must keep the name-based path for compatibility, add a
cheap end-to-end check that would have caught the exact silent failure (e.g., actually try to use
the capability and verify it happened, rather than trusting that "it should have detected it").
This applies directly to any fleet/monitoring tool that decides what checks to run against a host
based on parsing its hostname — a renamed or aliased host will silently get the wrong checks.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
