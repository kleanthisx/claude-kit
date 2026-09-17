---
name: gem-single-source-of-truth-prevents-duplicate-state
description: "Route every view of an entity through ONE shared store rather than letting each screen/panel hold its own copy — duplicated state drifts and users notice the mismatch before you do"
metadata:
  node_type: memory
  type: feedback
---

When several parts of a system need to show or act on the same entity (a record, a metric, a
host's status), give them ONE shared store to read from, not independent copies each screen
fetches or computes on its own.

**Why:** Building a multi-screen app (2026-07), each screen originally held its own local copy of
shared entities. The user's key complaint was that the same activity showed up differently
depending on which screen you were looking at — the copies had drifted out of sync with each
other. The fix was a single central store (one canonical object per entity, derived values like
counts computed FROM it rather than tracked in parallel) with every screen reading and writing
through that one store. After the refactor, every screen agreed with every other screen by
construction, because there was only one place the data could live.

**How to apply:** Whenever the same fact needs to appear in more than one place — a dashboard tile
and a detail view, a summary panel and a drill-down, a status light and a log line — make one of
them the source of truth and have the rest derive from it, rather than each computing or caching
its own answer. This applies well beyond UI code: a health-monitoring dashboard that shows "3
alerts" on one panel and "5 alerts" on another because each panel queries independently is the
same bug as the duplicated-activity case above. Before adding a new view of an existing fact, ask
"where does this value ALREADY live" before writing a new query or a new local copy for it.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
