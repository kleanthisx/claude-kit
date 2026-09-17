# OPS — ticket board + usage ledger

> **TEMPLATE — adapt at the site.** This is the FORMAT only: the rules, the table columns, and one
> illustrative example row. No real tickets are shipped with the kit. Copy this to `<OPS_BOARD>`
> (commonly the workspace root, e.g. `OPS.md`), delete this notice and the example row, and start
> logging real work.

**Plan/pricing note (fill in for this account):** record what the vendor actually publishes for
this subscription tier — usually a *relative* multiplier ("N× more usage per session than the base
tier") rather than an absolute token figure, plus that overage beyond plan limits bills at standard
API rates. Because no absolute budget is published, **capacity is only knowable by calibration**:
pair the statusline/usage-footer percentage with the local token tally at the same moment
(capacity ≈ tokens / percent), and log calibration points in the usage ledger below as they appear.
If a runaway session ever burns real money before this is understood, that is exactly the kind of
incident this file exists to make visible sooner next time — record the date and rough cost, not
just the fix.

**Protocol:** every fan-out / heavy job is a ticket. Execution happens on **lower-tier agents**
where the work allows it — the main loop is the most expensive unit in the house, so it delegates,
judges and compiles rather than doing bulk work itself. State the model-tier ratio you're actually
paying (e.g. "opus output costs Nx sonnet output") once you know it, so budgeting decisions use real
numbers instead of a guess. **Budgets are OUTPUT tokens.** **At 80% usage: pause all ops** — a brief
resume every ~30-45 min keeps the prompt cache warm if the reset is close; otherwise wait for reset.

## Tickets

| ID | Job | Tier | Budget (out) | Status | Actual (out / all-in) |
|----|-----|------|--------------|--------|-----------------------|
| T-001 | Example: fan out N read-only research agents over a bounded question set, one synthesis pass over the results | sonnet gatherers + opus synth | 100k | DONE YYYY-MM-DD | 86k / 410k |

<!-- Add real rows above this line, newest at the bottom. Keep the columns exactly as shown so the
     ledger stays greppable: ID, one-line Job (what + how bounded), Tier (which model(s) did the
     work), Budget stated BEFORE the run, Status (DONE/PARTIAL/PARKED/IN PROGRESS + date), and
     Actual reported AFTER the run (output tokens / all-in including subagents). A ticket without a
     stated budget is a ticket that will not be caught overrunning one. -->

## Usage ledger (append-only; banners are authoritative for main-loop usage)

<!-- One line per notable usage event: a limit-banner sighting, a calibration point (footer % paired
     with the local tally's token count at that moment), or a session-close summary from /wrap.
     Example shape:
     - YYYY-MM-DD: footer showed N% used; local tally read M tokens at the same moment (calibration point).
     - YYYY-MM-DD: session close via /wrap — <one-line summary>. -->
