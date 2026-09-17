---
name: length-estimate-in-prompt-not-cap
description: "Control reply length with an estimate IN THE PROMPT (\"aim for ~150-200 words, one beat\"), not a max_tokens cap — a cap truncates, an instruction sets the target; keep the cap as a safety only (user, 2026-09-12, the chat webapp register)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c70b1007-9573-41fe-8972-5240b6dc2ff7
  modified: 2026-09-11T21:04:37.669Z
---

User (2026-09-12, while shortening the chat webapp replies to the reference product's ~1000-char register): "if you want a reply
estimate put it in the prompt."

**Why:** `max_tokens` cuts the reply mid-sentence and the model still plans a long answer; a length target in the
prompt changes what it aims for. The first draft of the register change (2026-09-11) coupled a 220-token cap with
the style block — the cap was the wrong lever.

**How to apply:** for any register/length control on a chat model: put the target words, the beat count and the
"leave the turn open" rule in the system/style block; keep `max_tokens` loose (a safety, not the control). Make it
an env/flag so a benchmark run changes one variable. Since 2026-09-12 the register is PER CHARACTER (profile `register` field, `REGISTER_DEFAULT` for profiles without one; `PROSE_REGISTER=off` is the A/B off-switch) — user: "a dominant personality doesn't ask, it states, it commands… it's best to be per character". Related:
[[one-change-per-run-subtract-to-find-fault]], [[log-experiments-not-just-conclusions]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
