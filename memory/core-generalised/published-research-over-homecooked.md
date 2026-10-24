---
name: published-research-over-homecooked
description: "When a design needs a mapping, scale or model, look for the published one first and build on it; an invented formula is a hack. If it does not match the data, improve the method or the data - do not bolt on a special case (2026-10-05)"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-05T11:29:48.651Z
---

Operator, 2026-10-05 (an RP project, character engine): *"i don't want to abandon solid research for homecooked solutions. homecooked solutions are hacks. and we don't do hacks. we do processes. we are scientists. if something doesn't match the data we improve the method, data or both. wanna go fast go alone, wanna go far go with many. solo is yolo, many is a structured system"*

**What happened:** a tracker could not tell a guarded character from a free one. In one hour I proposed, in order: a universal prompt rule ("too early = negative"), a 4th "inhibition" axis with a baseline formula of my own, a standing free-text line, and then replaced the engine's Big Five words with card text. Each was a special case for one scenario. The operator's objections: *"I am feeling that we drift into hardcoding things again"*, *"We had 3 very generic axis in place... Now a forth for specific scenarios then a fifth"*, then *"isnt there some emotions wheel or something that can correlate big 5 to aspects of the character? it's a 5D space ffs"*. The published answer existed (AB5C circumplex, IPIP facets): the five numbers already carried it, and the engine was reading them one axis at a time.

**Why:** the engine is built on published models on purpose (Big Five -> PAD, a published affect-mapping model). A homemade axis or formula has no evidence behind it, multiplies per scenario, and abandons the generic structure that was chosen.

**How to apply:**
- A test that fails is a reason to examine the method (how are we reading what we already have?) before adding anything.
- Before proposing a new variable, formula or table, ask: is there a published model for this? Fetch it, with locators ([[research-method-rules]]), and build on it.
- Count the things I am adding. A second special case in one sitting means stop and look for the general structure.
- Experimental changes go in a tracked copy with a way back (operator, same day: *"we cant have production code change without a way back"*) - a git worktree on its own branch, not the shared working tree.

Related: [[use-the-specialised-tool-not-my-code]], [[models-read-and-write-code-keeps-state]], [[build-on-the-existing-system-not-a-replica]], [[check-project-prior-art]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
