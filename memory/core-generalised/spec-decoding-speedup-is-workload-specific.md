---
name: spec-decoding-speedup-is-workload-specific
description: "Never quote a speculative-decoding (MTP/draft) headline speedup as workload-general; acceptance collapses on prose (~37%) vs code (~76%), so state the workload"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-05T10:14:29.746Z
---

Speculative-decoding speedups (MTP3, draft-mtp, DFlash) are NOT workload-general. Acceptance rate — the fraction of draft tokens the target accepts — is a model/workload property (roughly GPU-independent) and it collapses on high-entropy text.

Measured in a 3090-only inference engine's `performance.md` (Qwen 27B/35B):
- Structured ~90%, Code ~76%, Translation ~75% acceptance (~3.1–3.7 tokens/round)
- **Prose/story ~37–38% acceptance (~2.1 tokens/round — barely above the no-spec baseline of 1)**

A vendor's headline "single-user 2×" is usually a code/structured/reasoning number. The engine's 70 tok/s C1 headline was at 61% acceptance (reasoning/mixed), NOT prose; the engine never publishes a prose spec-speedup at all.

**First-party measurement (an older, VRAM-starved work machine with two small pre-tensor-core cards):** enabling MTP gave only **~6% decode gain on coding, prose was a wash — and the 6% was PAID IN VRAM** (the draft head + speculative state occupy memory). On that starved box, 6% speed for scarce VRAM is a bad trade → user skips MTP there. **SCOPE CAREFULLY:** the prose=wash half transfers to any GPU (acceptance is model/workload, GPU-independent); the "not worth it for coding" half was VRAM-driven on the starved box and does NOT automatically transfer to the 24 GB Ampere 3090 — that case is untested (the local build can't run spec decode) and remains OPEN, not settled. Also: those old cards predate SM86, so the engine (SM86-only) physically cannot run on the work box; the entire engine question lives only on the 3090. The rejection cost isn't a symmetric "half the target work wasted" (the target verifies all K draft tokens in ONE parallel, memory-bandwidth-bound pass; you always keep ≥1 real token even at 0% acceptance). The real killers are: fewer tokens committed/round at low acceptance + fixed per-round draft overhead + prose runs hot (high temp) → net ≈ 0. The engine's ReplaySSM is explicitly built to cut spec-decoding's VRAM cost (`README.md:69`) — the one lever that could change the coding math — but that's the engine's claim, unverified by us, and it does nothing for the prose-acceptance problem.

No first-party MTP run exists on the home 24 GB card: the llama.cpp build there rejects spec decoding; the local-serving note says the same.

**Verified from disk (2026-09-05), two hard facts that block a naive "just enable draft-mtp":**
1. **Our GGUFs have NO MTP head.** Tensor-family dump of the two local GGUFs (a 27B dense coder, a 35B MoE) shows only the standard `output.weight` head — no nextn/mtp/draft head. So `--spec-type draft-mtp` can't run on what's on disk; MTP needs a NEW artifact (an MTP-head re-conversion, or a separate same-family draft model) = disk cost. (Beware false positives: `smtp`/`predict`/`draft` appear in the tokenizer vocab, not as tensors — grep the actual strings/tensor names, never trust a substring count. I made exactly that error before dumping tensors.)
2. **These "Qwen3.5/3.6/3.8" models are HYBRID attention + SSM** (tensors `ssm_alpha/beta/conv1d/dt/norm/out`; 35B adds `ffn_*_exps` MoE). Speculative decoding on a hybrid-SSM model must snapshot/replay the SSM recurrent state per drafted token — an intrinsic VRAM cost pure transformers don't pay. This is almost certainly the user's "6% PAID IN VRAM" (SSM-state replay, not generic draft overhead), and it's exactly what the engine's ReplaySSM is built to cut. llama.cpp has no ReplaySSM equivalent → the SSM VRAM tax recurs there even on a roomy card. The clean SSM-aware spec-decode lives only in that engine, which won't load GGUFs.


**Why:** the user (technical, prose-heavy local products) caught me quoting a code-flavored 2× as his single-user gain — "that's bull. mtp works on code but not prose." Then supplied his own numbers (~6% coding, paid in VRAM; prose a wash). His flagship local use is exactly where spec decoding is weakest, and even the coding win doesn't clear the VRAM cost on a tight card.

**How to apply:** when citing any spec-decoding speedup, name the workload, the acceptance rate, AND the VRAM cost. For a prose/roleplay use case treat the win as ~zero; for coding on a VRAM-tight card treat it as marginal-and-not-free. This is a specific case of [[report-verifiable-only]] — a benchmark number carries its benchmark's conditions; stripping them is fabrication-by-omission. Also ties to a related project note (his real task, not a leaderboard) and a second related project note (prose product).

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
