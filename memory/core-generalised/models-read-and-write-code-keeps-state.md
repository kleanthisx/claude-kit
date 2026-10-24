---
name: models-read-and-write-code-keeps-state
description: "In LLM systems, code holds state and decisions as DATA; the model reads all intent and writes all language - never regex for meaning, never English sentence templates (operator: \"it's not 1998 when everything was hardcoded\", 2026-10-04)"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-04T20:08:55.684Z
---

Code decides and stores; the model reads and writes. Never hardcode language or meaning:
- No regex/keyword lists to decide what the user MEANS (invites, items, "where do you live", topics, who a
  description refers to, stock phrases, names said). One structured model pass (json_schema) reads intent.
- No English sentence templates for outcomes ("X DECLINES ... she does not take people home until she trusts
  them"). The engine returns the decision as data ({request, outcome, scale, value, needed}); the narrator writes it,
  in voice, with the right pronoun.
- Code keeps numbers, gates, the graph, the clock.

**Why:** 2026-10-04, an RP world project's relations module / play7 harness: a refusal reason hard-coded "she" came out for a male
NPC. Operator: *"you hardcode something this basic? ... imagine the hardcoding it would take to run a scenario. that's
why we use models. it's not 1998 when everything was hardcoded."* Enumerated the class the same turn: 14 places
(7 prose templates, 7 intent regexes) built up across play4-play7, each passing the phrasing I tested and failing the
next one.

**How to apply:** before writing a string the user will read, or a pattern that guesses meaning, stop - that is a
model's job; pass structured data instead. A regex is fine only for format (ids, times, JSON), never for meaning.
Related: [[use-the-specialised-tool-not-my-code]], [[finish-the-defect-class-not-the-instance]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
