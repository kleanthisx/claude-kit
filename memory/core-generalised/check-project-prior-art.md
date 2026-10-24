---
name: check-project-prior-art
description: "Search the project for prior art (runbooks, measured numbers, existing scripts) BEFORE external research or estimating"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-10-12T16:25:09.914Z
---

When costing/designing anything, grep the project tree for prior art first — runbooks, measured benchmarks, existing scripts — before web research or first-principles estimates.

**Why:** 2026-08-06, a large story archive processing costs: I estimated rented-GPU throughput from scratch and priced a two-pass pipeline, while `<an-RP-project>/classify/CLOUD_RUN.md` already held MEASURED throughput (266 ch/hr per rented GPU), a superseding single-pass extractor (extract.py), and automated box setup. User had to point it out ("there's info in the project"). The measured numbers changed the recommendation materially (~$150 estimate → ~$1.5k reality for full-rich).

**How to apply:** before answering cost/feasibility/design questions in an existing project, run a quick Grep for related keywords (tool names, "RUN", "PLAN", "HANDOFF", *.md runbooks) and read what exists. Estimates only where no measurement exists — and say which is which. Related: [[work-style-kiss-mvp-rtfm]] (RTFM applies to the user's own repos too), a related project note.

**Again 2026-10-03:** wrote a new image fetcher for 125 member cards while `<export-dir>/fetch_images.py` (proven, resumable) already does it from `fresh/cards.jsonl`. Operator: *"we have fast scripts for these things. proven scripts. why would you write something new?"* Before writing any fetch/build script, `ls` the project dir for one that already does it and feed it the input it expects.

**Again 2026-10-12 (image bench, checkpoint version test):** I designed a new stage from the conversation, not the entity page. `ledger:<an-RP-project>/image-bench` already held: the reference site's images of one character are different people, canonical = `0.jpg` (`the-reference-set-is-not-one-person`); their card weights on checkpoint v6.5 overshoot and v6.0 was already tried (`<look-entry>` U-W); their base images are 916x1144; the recipe is nude-first + W4 + face pass. I put all five of their media files in as targets and rendered without the nude word. Operator: *"we already established they are different people in the other shots"*, then *"read the fucking wiki"*. **How to apply:** before writing a new stage script on a project with a v2 wiki, re-read the owning entity's decisions for the subject (grep the entry names, then read those entries whole) and list in the script docstring which recorded findings it builds on or re-tests.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
