---
name: render-the-data-dont-query-it
description: Sort the whole list and read it before building any heuristic; frequency order hides the patterns that adjacency reveals
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e13cd0c7-a27e-454e-a43f-39d75c4e7936
  modified: 2026-09-14T16:48:44.949Z
---

Before writing a single rule, classifier or statistic over a dataset: **dump the
whole thing to a file, sort it so like sits next to like, and read it.**

Caught 2026-09-14 (a corpus project tag vocabulary, 352k tags / 45k words).
The user opened the word list in Notepad++, sorted it, and in ~10 minutes found
structure I had missed across a day of work:

- years (`1969`, `1964`…) that should collapse to decades
- bra sizes (`34dd`, `36jj`) that mean small/medium/large breasts
- participant notation (`1m1f` -> `mf`, `3females` -> `fff`)
- `cuckhold`, a 499-use misspelling immune to my corrector
- run-together compounds (`chastitybelt`, `daddaughter`, `brotherandsister`)

**Why I missed it, measured afterwards:** every look I took was a *query* —
aggregates, `LIMIT 20`, samples — and every one was ordered by FREQUENCY.
Frequency order is the single ordering that guarantees morphological families
are scattered. Verified: across my 8 agent slices, bra-size members were spread
over 4 files with **0%** adjacency; year members over 6 files with 20%. Sorted
alphabetically or by 4-letter stem, each family clusters and is obvious on sight.

**Why the subagents missed it too:** I gave them a per-line task ("label each
word"), which structurally forbids noticing cross-row patterns, and I sliced by
frequency so no agent ever saw two family members together. I also told them
numbers and names map to nothing — training them to dismiss the rows that had
the structure.

**Why:** the user's cost is real and mine is not. A day of heuristics that a
sorted file would have made unnecessary is the expensive kind of wrong.

**How to apply:**
1. Write the full list to a file. Not a sample, not a summary, not `head -20`.
2. Sort it several ways — alphabetical, by stem/prefix, by length. Adjacency is
   the instrument; frequency order destroys it.
3. Read it, or have an agent read it *in an order where families are adjacent*.
4. Only then decide what needs a rule. When the user says "go in and read it",
   that is the instruction — not a hint to build something that reads for me.
   The one hand-read pass in that session (459 misspelling pairs) produced the
   best output of the day; no statistic could separate `queer/queen` from
   `cuckhold/cuckold`.

Related: [[settled-principles-are-answers-not-questions]],
[[one-change-per-run-subtract-to-find-fault]],
[[coverage-is-sampling-not-headcount]], [[work-style-kiss-mvp-rtfm]]

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
