---
name: gem-hub-and-spoke-prevents-doc-drift
description: "A fact true across many systems belongs in ONE shared hub that spoke-level docs link to, never copy — copied facts go stale independently and each copy has to be caught and fixed separately"
metadata:
  node_type: memory
  type: feedback
---

When the same fact needs to be known in several separate places (which hardware/model/tool is
current, which config is authoritative, which contact is on-call), put it in one shared,
authoritative page and have every other document **link up to it**. Never let a second document
copy the fact inline — the moment it changes, every copy but one is now silently wrong.

**Why:** Across several projects that each needed the same generic facts (which local models were
current, how a shared service was configured), those facts had been independently duplicated into
each project's own docs. Stale references to since-abandoned tools kept surfacing because a fact
was updated in one place and never propagated to the others. The fix (2026-08-25) was a single
cross-project hub holding anything true for two or more consumers, with each project's own docs
reduced to project-specific detail plus a link up to the hub — hub-and-spoke, never copy-and-paste.

**How to apply:** In any environment with multiple systems/runbooks that share facts (which
patch level is current, which credential rotates on what schedule, which server is the primary),
maintain one hub page per shared fact and have every runbook link to it instead of restating it.
When you catch yourself re-explaining something in a second document that a first document already
covers, that is the signal to move it to the hub and link, not to keep both copies "in sync" by
hand — hand-sync always loses eventually.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
