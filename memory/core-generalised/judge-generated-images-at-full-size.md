---
name: judge-generated-images-at-full-size
description: "Contact-sheet thumbnails are for triage only — never score a generated image a win until it has been opened at full size and checked for anatomy (joints, limbs, hands, where bodies join)"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-17T11:08:15.533Z
---

When evaluating image-generation outputs, a thumbnail contact sheet only triages composition, outfit and
scene. **Anatomy is judged at full size, on every candidate before it is called a win or used as a parent.**
Check: knees/elbows bend the right way, limb count and length, hands/fingers, where bodies join.

**Why:** 2026-09-17, an RP project's character image bench (Qwen-Image-Edit-2511). I scored `Q1_<character>` from a
300×375 thumbnail. The operator: *"in sheet q1 [character] the 4th image has the kneecaps at the back of her legs"*
— a rear-view body with legs rotated 180°. Re-checking at full size, the image I had called the Q3 "win"
(`Q3_<character>_facing`) also failed: malformed anatomy. Two false wins from one method, both caught only
by opening the file. A local search that mutates around a false win explores around a broken parent.

**Identity is judged side by side, not from memory.** Same session: I called an img2img pass over a
base checkpoint "identity held"; operator: *"the 0.7 pass fixed the body but the face is no longer [the character]."* A face crop of the
reference next to the output showed a different woman (blunt auburn bob vs wispy bangs). Build a crop strip
(reference | candidate) at the same size before any identity verdict.

**How to apply:** sheets → shortlist → open each shortlisted image with Read at full size → anatomy verdict
logged per image → only then mark WIN/parent. Say in the log which verdicts are thumbnail-level. Related:
[[report-verifiable-only]], [[verify-against-authority-not-recall]], [[render-the-data-dont-query-it]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
