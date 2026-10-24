---
name: work-style-kiss-mvp-rtfm
description: "KISS, MVP and complete-in-every-aspect are ONE constraint — whole, not partial. They limit depth and mechanism, never coverage. Plus RTFM and settle-it-with-a-test."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-12T17:18:23.953Z
---

The user demands **KISS, MVP and RTFM**. They are a power user, not casual.

## KISS / MVP / "complete in every aspect" are the same constraint

Not three competing goals — three names for **whole, not partial**.

- **MVP** — the load-bearing word is *viable*. The smallest thing that works **end to end** and
  teaches you something real. A fragment is not viable, so a fragment is not an MVP.
- **KISS** — about *mechanism*: do the whole job with the fewest moving parts. It says how to
  build, never what to leave out.
- **Complete in every aspect** — nothing the whole requires is missing. Rough is fine; absent is not.

**They constrain depth and mechanism. They say nothing about coverage, because coverage is not
negotiable.** Shallow everywhere: yes. Missing somewhere: no. Less *depth*, not fewer *parts*.

**The failure mode this rules out is depth in one corner** — which violates all three at once:
over-invested in one place (not minimal), elaborate mechanism before the shape exists (not simple),
everything else absent (not complete). Same idea as [[code-structure-no-piecemeal]]: a vertical slice
that runs IS complete-in-every-aspect at minimum depth; horizontal modules sitting dead are the fragment.

**Trigger (this is the enforceable part).** Before starting any build or draft, **enumerate every
aspect of the whole as a checklist first**, then go shallow across all of them in one pass. Enumerating
first is what makes "missing somewhere" visible; without the list, depth-in-one-corner feels like progress.
This binds to the existing checklist requirement in CLAUDE.md.

## RTFM

Verify against the actual tool/docs before asserting limits. Run `--help`, read the manual, check the
CLI. Do not answer capability questions from memory.

**A configured value is a dial, not a wall.** Before calling something a limit, ask whether a known
setting moves it, and lead with the dial and its price. 2026-10-12: asked to explain why big compiled
character cards from a reference site were a problem, I built the answer around the 32k context slot. Operator: *"you're always
so occupied with limits. we can offload all experts drop to 35 t/s and have all the context"* - the MoE
expert offload (`-CpuMoe N` in the RP launcher script) trades speed for context, and it was already
recorded in the RP project's `TASKS.md`. Size was never the question; whether the output plays well was.
I then called the 35 t/s "your figure, not measured" - it was measured: `<an-RP-project>/SESSION_HANDOFF_local-llm.md:20`
(2026-07-31, 3090, Qwen3.6-35B-A3B, `-ncmoe 41` = all experts on CPU, turbo2 KV: 33.7 t/s at 32K, KV room
for 1.5M+ tokens). Search the project before labelling an operator's number unverified.

## "A good test is worth 1000 expert opinions"

Settle questions empirically — run it, test it, measure it — rather than arguing from authority or
opinion. When there's a disagreement or an unknown, build the smallest test that proves it. Fits the
user's Ti-dominant streak (a related note): trust mechanisms you can verify over consensus.

**Why:** Over-engineering and unverified claims waste their effort. Two concrete failures:
(1) asked for "remote, no permissions", I insisted no remote flag existed and pushed a Tailscale
install — `claude --help` showed `--remote-control` all along.
(2) 2026-08-11: told to produce "draft 1, complete in every aspect", I treated MVP as "do less stuff"
and read a contradiction into it. Earlier the same day I built a calorie test bench for two meals while
the tree, composer, day view and warm path did not exist at all — depth in one corner, presented as progress.

**How to apply:** Enumerate every aspect, then build shallow across all of it. Smallest correct answer
first; check the docs/CLI before claiming something can't be done. Related: [[build-mode-concept-vs-plan]],
[[claude-launch-workflow]].

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
