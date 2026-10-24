---
name: internal-docs-are-not-evidence-about-external-systems
description: A claim about an external site/API/product is verified against that system at the time of use — our own wiki is never the source for it; repeating one as fact is how a lie becomes doctrine
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-30T21:49:39.501Z
---

**A claim about an EXTERNAL system is verified against that system, at the time of use, or it is not
stated.** Our wiki, notes, code comments and prior sessions are authoritative for OUR decisions.
For a fact about someone else's site or API they are at best a stale observation, at worst an
untested inference that has hardened into a citation.

Operator, 2026-10-01: *"the real gap is that like you grep files you grep sites as well. worst of all
is that you lie. and people believe the lies.."*

**What happened:** the RP project's wiki said *"the per-option art on the reference site is paywalled"*.
I repeated it to the operator as established fact and proposed a design around it. They replied with
a screenshot of the live page showing full art on every preset, categories, a Trending sort, search
and community presets. Never gated — merely never captured. I had a logged-in browser open; the check
was one navigation.

**Why it matters more than being wrong:** I did not just answer wrong, I *sourced* the wrong answer.
It had been in the wiki about a month, it shaped a build decision (arbitrary photos on labelled
tiles), and stating it again would have re-certified it for the next session. That is the mechanism
by which a fabrication becomes project doctrine, and the operator is the only one positioned to catch
it — which makes the cost theirs.

**How to apply:**
- Grep sites the way you grep files. Browser access is a verification tool, not just a task tool.
  Before claiming anything about an external product's behaviour, pricing, gating or UI — go look.
- A claim inherited from our own notes gets a locator AND a freshness check before it is restated.
  Under [[two-week-trust-horizon]] anything older than ~2 weeks is untrusted; an external-system
  claim is untrusted at ANY age, because their site changes without touching our repo.
- Say "our notes say X, unverified" — never "X". The hedge is the whole difference between a stale
  note and a lie.
- When a claim like this is disproven, correct it **where it is recorded**, not only in conversation.
  The conversation scrolls away; the wiki entry is what the next session believes.

Same family as [[report-verifiable-only]] and [[verify-against-authority-not-recall]] — this is the
external-system case, which those did not close. Related: [[check-project-prior-art.md]] says read our
notes FIRST; this says our notes are a lead, never the evidence.

> *Generalised for portability: the incident behind this rule is described without naming the
> project. The lesson, the numbers and the user's words are unchanged.*
