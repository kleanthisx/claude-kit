---
name: two-week-trust-horizon
description: "Anything older than ~2 weeks is untrusted — code, docs, logs, and my own memory of it; re-verify it against the CURRENT project landscape and technical environment before reuse (2026-09-16)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b7a5945e-70c6-497f-bd36-5c567aea3981
  modified: 2026-09-16T09:11:25.106Z
---

**If something is more than a couple of weeks old, we do not trust it** — not the script, not the
docs, not the logs, not our memory of it. **Two weeks is the assumed memory span.**

Coming back to reuse an older artifact means investigating it thoroughly first and confirming it
still matches **the current project landscape and technical environment**. Not one named dependency —
the whole surface it sits in: what else exists now, what has been renamed, split, deprecated or
deleted, which conventions and decisions have changed, what the tooling, models, paths, versions and
runtime look like today. An old script that still parses and still runs is not evidence that it is
still correct.

**Why:** the user (2026-09-16). Nothing in this workspace holds still, and the drift is never
confined to the one thing an artifact obviously touches — a script can be broken by a directory
that moved, a table that gained a sibling, a model that was deprecated, a rule that was reversed.
Scoping the re-check to the artifact's own subject matter is how a stale thing passes inspection.
See [[verify-against-authority-not-recall]] and [[report-verifiable-only]].

**How to apply:** check the date on anything before leaning on it — file mtime, the log entry's
date, the decision's bracketed date. Older than ~2 weeks: say so out loud, then verify against live
state rather than against the artifact's own claims. Applies to my own earlier statements in a long
session too. Never present an aged figure as current — quote it with its date, or re-measure.
Related: [[persistence-in-curated-space-is-selection]] still holds, but age alone confers no trust.
