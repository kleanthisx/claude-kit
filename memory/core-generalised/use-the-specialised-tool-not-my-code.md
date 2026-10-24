---
name: use-the-specialised-tool-not-my-code
description: "Reach for the specialised library, program or published asset first - people spent lifetimes on them and they beat anything I make; test existing LoRAs, never train our own (2026-10-16); when the operator names a tool or a method, execute that, not my own version"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-10-16T14:45:00.000Z
---

When a job has a mature specialised tool — image processing, colour science, depth, detection,
audio, geometry — **use that tool**. Do not write my own version of it. Generic code I produce on
the spot loses to something a field has refined for decades, and the operator is usually the domain
expert in the room.

Operator, 2026-09-18: *"people could work and produce things before and build specialised tools for
many many many jobs. and those tools are not generic ai code. people spend their lives on them. and
they do work, better than anything you can come up with. so do as youre told."*

**Measured in that session (an RP project's image bench), every single time:**

| I hand-rolled | what happened | the tool |
|---|---|---|
| skin mask + garment split + hole morphology + offsets, ~80 lines | blocky stair-stepped patches on skin areas, visible at 2x | `skimage.exposure.match_histograms` on the whole image: brightness 117.7 vs target 117.2, a*/b* exact, blown highlights 18% -> 1%, one call |
| per-channel numpy grain | red/blue chroma speckle, 5x the reference, invisible to my own luminance metric | luminance-only grain; ImageMagick `-attenuate +noise` in YIQ |
| bodytype metric, THREE attempts | all failed: skeleton hips are joints; mask row extent is arm-to-arm; midline run collapses below the torso | still unsolved - correctly left to the eye rather than faked |
| my own lens strength k=9 | over-blurred, cost identity, "everything is noisy" | the estimator read k=2.0 off the reference; I ignored it |

**Second instance, the image bench, 2026-10-03 to 10-14 (operator, 2026-10-16):** the bench's job was to TEST
existing LoRAs and find what works. I trained our own instead (a style LoRA v1, a face LoRA v1, then a "v2: more
steps / higher rank" task line), without a usable training image set. The operator: *"the idea was to test
loras to find what works. not build our own"*, and, on my claim that ours could reach the level of LoRAs made
by actual people: *"overshooting the target ... look at your track history, in programming which is your best
skill.. and you go off to build a lora without having images."* **Why:** thousands of trained, tested LoRAs
exist; selecting among them is bounded work the bench can finish. Training is a craft I have no track record
in, and my result is worse than the field's, not equal to it. **How to apply:** on this bench, a LoRA is
something we download, read the card of, and test as one arm. "Make our own X" is never the next step unless
the operator orders it; if the search finds nothing, report the gap and the candidates, do not fill it by
building.

**The operator is a photographer of ~20 years.** On lighting, exposure, colour, lens and film they
call it by eye correctly and faster than my measurements do - blown whites, green cast in skin, the
collage cut-out, chroma speckle, the blocky mask edges: every one spotted before or instead of a
number of mine.

**How to apply:**
1. Before writing image/signal/geometry code, ask what the established library or CLI is, and use
   it. On this machine: opencv (+`xphoto`, `photo`), scikit-image, color-matcher, mediapipe
   (DeepLab, pose, selfie), MiDaS via cv2.dnn, ImageMagick, G'MIC (1189 film CLUTs). On Linux both
   ImageMagick and G'MIC are one `apt install` away.
2. Feed the tool the WHOLE input and let it derive from the reference sample. Do not pre-segment,
   pre-mask or pre-split unless the tool asks for it - that is where my artifacts came from.
3. When the operator names a tool, a method or a parameter, execute exactly that. Propose an
   alternative in one line, then do theirs anyway unless told otherwise.
4. Judge the result the way a viewer sees it - full size - not by pixel-peeping a 100% crop.
   See [[judge-generated-images-at-full-size]].

Related: [[stated-method-is-the-method]], [[render-the-data-dont-query-it]],
[[never-author-my-own-exemption]], [[work-style-kiss-mvp-rtfm]] (RTFM: the tool has a manual).

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
