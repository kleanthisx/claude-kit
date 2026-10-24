---
name: uncensored-is-a-claim-read-the-card
description: "Before serving/benchmarking any 'uncensored' local model, read its HF card for the METHOD (abliteration/Heretic/ARA vs partial orthogonalization vs nothing) and its failure notes; a name is not a property. The 2026-09-12 gemma matrix compared aligned vs abliterated, not model quality (user caught it)"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-12T06:46:07.628Z
---

User (2026-09-12, an RP project's persona matrix): "the difference i think is that gemma models are not unrestricted.
please check… just check them from hf registry." They were right: gemma-4-26B-A4B-it was Google's official
aligned instruct (no abliteration at all); "Gemma-4-31B-Cognitive-Unshackled" was a partial orthogonalization
whose own card documents the `l L de` "safety marker" token salad we had just logged as "instability"; Qwen3.8-27B
RVN was Heretic ARA with 0-1/100 refusals. I had read the gemma hostility as "plays the label" and the salad as
"quant/KV cache" — wrong causes for right observations.

**Why:** an "Unshackled"/"Uncensored" name says nothing about the method or how complete it is; a benchmark
across models with different alignment states measures alignment, not roleplay quality. Refusal-in-character
looks like a hostile persona.

**How to apply:** before a model goes into the model registry as an RP candidate, record from its
HF card: base model, uncensoring method (abliteration/Heretic ARA/orthogonalization/none), refusal numbers if
given, documented failure modes. Count refusal-family phrasing in outputs when a model reads "hostile". Related:
[[one-change-per-run-subtract-to-find-fault]], a related project note.

**2026-10-18, a fine-tune marketed for RP.** I picked a 24B RP fine-tune as the simulated-user model for a 5-hour test because the launcher labels it "SOTA RP". Operator: "[that model] is a piece of shit.. i never got it to work. it is a specialty tool i never trusted. and when i asked you to get it to work you couldnt either. just cause it names itself an expert, it's not." Rule: a model's self-description ("RP specialist", "uncensored", "expert") is a claim; the operator's record of it working is the evidence. That fine-tune and a second marketed-for-RP one (entries [6]/[7] in the launcher menu) are not used for anything; the sanctioned chat set is the big 4 (fully-abliterated gemma-4 and qwen pairs, dense + MoE).

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
