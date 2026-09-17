# LAUNCH — <name of the multi-agent workflow>

> **TEMPLATE — adapt at the site.** This is the exact shape `guard-launch-gate.ps1` requires before
> it will allow a `Workflow` tool call with a `scriptPath` to run: a machine-computed audit of the
> script (not a description of it), the approval line, and nothing else load-bearing. Copy this to
> `<cwd>/LAUNCH.md` next to the workflow script, fill in the audit from the real file, delete this
> notice, and do not add `APPROVED: GO` until a human actually says go.

STATUS: awaiting user approval (gate: `guard-launch-gate.ps1`).

Script: `<absolute path to the workflow script>`

## Machine audit (computed from the file, not prose)

Compute every line below by actually reading/grepping the script — the gate denies a `name`-only or
inline launch precisely because those can't be audited before they run, and it re-derives its own
count from the file rather than trusting this document, so a stale number here just gets rejected.

- agent() call sites: **<N>** — note separately if any sit inside a loop, so the real spawn count is
  higher than the literal call-site count (e.g. "3 call sites, but one loops over a list → ~12 actual
  spawns").
- model: declarations: **<N>** — state whether every agent is pinned to a specific tier, or whether
  any inherit the session's model (inheriting is the risk the gate exists to catch).
- budget.spent() / remaining() references: **<N>** — where the cap is enforced in code, if anywhere.
  "No `+Nk` target set" is an honest and acceptable answer, but say so explicitly rather than leaving
  it implicit.
- SCRIPT-SHA256: `<hash of the exact file, e.g. from Get-FileHash / sha256sum>`

## What it runs

- One bullet per stage: which agents, how many, what each one does, per-agent caps (searches/fetches/
  turns), and the estimated output-token cost.
- State whether it runs in the foreground or background, and what surfaces at the end.

## Approval

To arm this gate, a human appends the line below this marker, after reading the audit above —
**not** after reading a description of the script.

APPROVED: GO
(User authorization received <date> — "<their literal words>".)
