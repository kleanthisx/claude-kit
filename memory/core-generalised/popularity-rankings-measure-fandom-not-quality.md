---
name: popularity-rankings-measure-fandom-not-quality
description: "before using any community rating/vote ranking as a quality axis, compute category/tag lift against the base corpus — a top-rated list usually marks small devoted fandoms, not better work"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e13cd0c7-a27e-454e-a43f-39d75c4e7936
  modified: 2026-09-13T10:57:05.261Z
---

Never treat a community rating, vote count or "top rated" list as a quality measurement until you
have compared its composition against the base population. Compute **lift** — the item's share of the
ranked set divided by its share of the whole corpus — per category and per tag. Large lifts on narrow
categories mean you are measuring **voter-base self-selection**, not merit.

**Why:** the archive's Top Rated list (2026-09-13, 133 stories joined to our 645,620-row corpus) put
one niche category at 36.1% against a 2.5% corpus share — 14.7x. That rare tag appeared in 26 of 133
top-rated stories while occurring only **124 times in the entire corpus: 963x lift**. A small devoted
fandom rates its favourites highly; broad casual-readership categories get diluted and sink
(two broad categories at 0.5x and 0.4x). Selecting on that rating would have produced a corpus
over a third that one category while the user had explicitly asked for a *wide* spread — the ranking would
have actively defeated the goal it looked like it served.

**How to apply:** (1) Compute per-category and per-tag lift before using any ranking as a selection
axis. (2) Prefer signals that agree across two independently-constructed rankings — the archive's
"Top Rated" and "Most Read" are built differently, and both showed long stories winning (median
`char_len` 4.2x and 2.4x over corpus), which is what made *length* credible where rating was not.
(3) State the sampling limit out loud: holding only the top N with no random or bottom sample shows
"the top ones have property X", never "X predicts rank" — that needs a control group.
(4) This applies to any vote-ranked source, including Civitai/Reddit model rankings cited in
`research/a model-survey folder/` — those votes were never checked against a base rate either.

Related: [[report-verifiable-only]], [[coverage-is-sampling-not-headcount]],
[[provenance-or-nothing]], a related note.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
