---
name: build-to-clone-quality-not-stub-mock
description: "Clone X / build a base" = comprehensive product-quality build in one coherent pass, not a stubbed mock patched incrementally
metadata:
  type: feedback
---

When the user says "clone X as a base for our product" (or build a base / foundation / "the real thing"), deliver a **faithful, complete, polished** replica in a coherent pass — real layout pixel-close to the source, real assets, real componentry, real interactions/state, and **NO "(mock)/stub/wires-later" labels anywhere**. It must read as a finished product. The only parts allowed to be silently non-functional are genuinely-unavailable backends (e.g. the model calls), and even those must look finished in the UI.

**Why:** On a clone of a commercial site (2026-08-29) I shipped a labeled "mock" full of placeholders and `(mock)` / "wires local SD later" text, then fixed it piece-by-piece (images, tabs, create wizard) only as the user kept pushing. They called it "half-assed" and reminded me they'd "essentially told you to clone the damn thing as a base for our product." Then, after I rebuilt the LOOK faithfully, they caught that controls were **decorative** (Explore filter dropdowns dead, Create's gender toggle did nothing) and said **"clone is clone, if i wanted just the look i could have taken screenshots."** That's the sharpest form of the lesson: **a clone must FUNCTION, not just look right** — every dropdown filters, every toggle switches, every button acts. Visual fidelity with dead controls is a screenshot. (Fixing it meant real work: capturing the reference product's Male/Trans create-asset sets so the gender toggle genuinely switches the flow, wiring real filter/sort state, etc.) Incremental minimum-viable patching is the wrong mode for a clone/base request.

**How to apply:** Treat "clone / base / foundation" as a directive for **completeness + polish across every aspect** (this is the real meaning of [[work-style-kiss-mvp-rtfm]] KISS = complete in every aspect, shallow allowed, missing-a-part not allowed). Enumerate every page/screen of the source up front, hold each to product quality, and don't call it done until the whole surface is there. Flag the spend before a big build, then go wide — don't dribble it out. Related: [[plan-before-code]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
