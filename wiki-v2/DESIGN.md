# Wiki v2 — the portable design choices

> **What this is.** The design decisions taken while rebuilding an entity-rich project's wiki from
> scratch, stripped of project specifics so they can be applied to another project. Each choice
> carries its reason and its source — adopt the ones whose reason holds in the target project, not
> the whole thing by default.
>
> **Research behind it:** `SYNTHESIS.md` §1-10 (agent memory, store choice, enforcement) and §11
> (design rationale, measurement comparability). A worked example with real byte counts and the
> migration phases guided these choices; it stayed with the source project and is not shipped here —
> if you rebuild one, keep your own worked-example log the same way.
>
> **The problem it solves, stated once:** a wiki that is too expensive to read is not read, so the
> knowledge in it is lost anyway — and the specific losses are (a) rebuilding something that already
> exists, (b) re-deciding something already decided, (c) comparing numbers that are not comparable.

---

## 1. The load classes are the design

Everything follows from deciding **when** each thing is read, not what it is about.

| class | read | cap |
|---|---|---|
| **Compass** — a generated overview of every entity's header | always | ~25-30 KB |
| **Map** — a generated list of every dead end, one line each | always | ~10 KB |
| **Doctrine** — methodology, testing process, principles of operation | always, **wholesale** | **hard cap ~15 KB** |
| **Entity files** — one per thing that exists | on demand, by name | ~12 KB each |
| **Ledgers** — measurements, scripts | on demand, whole table | — |
| **Ideas / Tasks** | on demand, by tag | — |
| **History** — logs, transcripts, raw run output | **never**; cited by path | — |

**Budget the always-loaded set explicitly and defend the number.** In one migration it went from
200 KB / ~51k tokens to ~52 KB / ~13k. If the always-loaded layer is not capped it regrows into the
thing you replaced — that project's previous rule ("if it is not a log, we read it") had become a
357 KB obligation.

**Doctrine is the one class that cannot be routed.** It is not attached to an entity; it governs work
on all of them. Route it by entity and it loads for none, because no task says "I am touching the
testing methodology".

## 2. A ten-line header in every file; the overview is GENERATED

Fixed field names, plain language, one screen. Fields are fixed **per kind**, sharing a core:

```
# kind:namespace/name
aka:         every name a person might use for it
state:       what is true NOW  ->  planned: where it is going (one clause)
owns:        the files this entity is responsible for
depends:     / dependents:   (dependents GENERATED from imports, never authored)
invariants:  what must not change, and what breaks if it does
open:        known defects/gaps, right now
verified:    date  (+ any rig/version in force)
run:         (runnable kinds only) the product's own launch command
```

- **Generated overview, not a maintained map.** A separate map file is a second source of truth that
  drifts; a header cannot drift from its own file. `head -10` across the directory *is* the overview.
- **`owns:` is what makes a read-gate buildable** — it is the file→page mapping an enforcement hook
  needs, declared inside the file instead of in a registry that rots.
- **`dependents:` must be generated.** A hand-authored dependency claim rots silently: one project's
  index asserted three consumers for a component that `grep` showed had one.
- **`state:` carries the trajectory.** Without it the always-loaded layer says "X only", the next
  session reads that as the design, and forks instead of adopting.
- **Empty fields are written `—`, never omitted.** Schema makes omission visible; prose hides it.
- **Naming:** Backstage's `kind:namespace/name` + DNS's canonical-name-plus-aliases (RFC 1034).
  **Ambiguity is a first-class row**: `"the pipeline" -> AMBIGUOUS: a|b|c|d — ask.` A lookup that
  returns AMBIGUOUS means ask, not guess. (In one project, one word had six referents.)

## 3. The body is a design log — dated AND named

Chronological order and name-addressing are not exclusive; ADR directories are numbered *and* named.

- **Entries are ADRs** (Nygard / MADR): `Title · Context · Decision · Status · Consequences` + an
  evidence path. **Never edit an accepted entry — supersede it** (`Supersedes:` / `superseded-by`).
  Editing around a decision is how a page ends up with a stale proposal sitting beside newer results.
- **Not every decision earns an entry** — durable ones only. (Horner & Atwood: *"it may not be
  advantageous to track preliminary and non-critical decisions"*.)
- **Killed ideas are entries with status `DISCARDED`**, in AutoResearch's negative-knowledge shape:
  `attempted_route · observation · failure · rationale · recommended_alternative`. Structured, and
  **re-injected into the next attempt** rather than filed away.
- **Diátaxis as the internal boundary:** header = reference (what is true now), body = explanation
  (why it came to be). No chronology in the header, no present-tense description in the body.

## 4. Write the attempt, not the account of the attempt

| | attempt | account |
|---|---|---|
| shape | a named one-line record | prose |
| bounded by | the number of things actually tried | nothing |
| where | `§Discarded` + the generated map | history / raw transcript |

The wiki grows by **entities, decisions, runs and attempts** — four countable things — never by
narrative. **Order survives without chronology**: `after:` on an entry, `Supersedes:` on a replacement,
`campaign`/`rig` on a ledger row.

**Why the map is always loaded:** you cannot search for a decision whose name you do not know.
Horner & Atwood, NordiCHI 2006: *"designers cannot recognize the relevance of rationale until a
person queries it… later uses may not be able to specify what information will be most useful."*
Dead ends must be **pushed** into the read set, never waited for.

## 5. Measurements: comparability is a key, not a date

- One ledger per measurement class, **indexed by subject**, rows never deleted — losers stay, that is
  what answers "has anyone tried a smaller/cheaper one?"
- **Every row carries the configuration that produced it** (MLflow/DVC: the pipeline version logged
  as a tracked param). Call it `rig`. **Two rows are comparable iff same rig.**
- **`RIG-BREAK`** — the boundary between two rig ids. Any comparison spanning one is refused unless
  the row carries an explicit `crosses-rig-break: <why this is still meaningful>`. *(No prior art
  names this failure; the mechanism — version-pin and group-by — is universal, the label is not.)*
- **Metric registry with a `role` column: DECIDER or CONSTRAINT.** Speed/VRAM/size usually
  *disqualify*, they do not *rank*. Optimising a constraint as if it were a decider is the classic
  benchmark error, and a column makes it impossible to do by accident.
- `source:` on every derived artifact — the same extractor over a different corpus is a different
  artifact, and mixing them silently is the data-side RIG-BREAK.

## 6. Scripts: record the interface, not the script

- **No purpose / owner / status / last-used columns.** `git log --follow -- <script>` answers all
  four exactly, and a column only goes stale.
- The durable notes are **`params:`** (machine-extract from argparse) and **`compat:`** (filled only
  when an interface changes and an old call breaks).
- **Precondition:** the scripts must actually be committed. In one project 33 of 41 were untracked, so
  "version control answers it" was false for four out of five of them.

## 7. Point at executable facts; never copy them

If a launcher, an `argparse` interface, a config or a git history already asserts a fact, the wiki
**points at it**. A copied fact is hand-maintained and drifts from the version that actually runs.
*(This rule was written after breaking it: a model×engine table was copied into a wiki page from a
launcher script that already held it, refusals and all.)*

## 8. Capture free-form; apply structure afterwards

Horner & Atwood: *"we do not want to force the content to be too structured but need to provide
structuring mechanisms so that it can be **automatically structured or restructured at a later
time**."* And Grudin, quoted there: design for **benefits to the current users, not just future
users** — a wiki whose payoff is entirely deferred does not get maintained.

**Therefore:** the person having the idea writes it however it comes out. The assistant adds the
tags, the schema and the entity routing afterwards. **If structure is ever demanded of the author at
write time, the design fails the way the literature says it fails.**

## 9. Three files that look similar and are not

| file | holds | test |
|---|---|---|
| `IDEAS.md` | things we **might** do — unevaluated | "I'm not sure, who knows" |
| entity `open:` | the **condition** — what is broken *now* | true whether or not anyone means to fix it |
| `TASKS.md` | the **intended action** + a done-condition | someone decided to do it |

Every idea and task **leaves**: promoted, tried, done, or dropped-with-a-reason.
**`DISCARDED` means tried and beaten; an untested idea is `OPEN`** — filing a shelved idea as
discarded loses the fact that nobody ever evaluated it.

## 10. Logs are ground truth, and they leave the wiki

The raw transcript already exists exactly; a hand-written narrative log is a **lossy second copy** of
it. So: no scribe writing prose from memory. The wiki is written in-flight as **field updates**
(bounded, overwritten), while the transcript stays the record and is rendered to readable text
**on demand**, not every session.

**One log entry fans out by type**: numbers → a ledger row; decision + reason → a named entry;
attempt that failed → a one-line record in the map; the account of it → history, cited by path.
**Extract before moving any log**, or the knowledge leaves with the file.

## 11. Concurrency comes free from the layout

- **One file per entity** — two windows on different entities never touch the same file. A single
  160 KB `decisions.md` that every session appends to is the opposite.
- **The cut is authored-vs-generated, not directory-vs-directory** — a test run and a code edit land
  in the same folder on different files; make that boundary explicit by giving generated output its
  own entity.
- **Generated paths are `.gitignore`d, not merely untracked** — untracked output clutters every
  `git status` while never being committed, which buries the diff you are trying to read.
- **Commit per finished unit**, so the other window sees current state.
- Branch/worktree-per-session is a legitimate option and pure overhead for a solo operator with
  occasional overlap. Hold it as an idea with a revisit condition, not a rule.

## 12. What NOT to build, with the threshold that changes it

| not building | why | revisit when |
|---|---|---|
| vector/semantic index over the wiki | prior art thresholds: ~500+ pages / 1,000+ files before semantic search wins meaningfully; every major coding agent loads plain markdown wholesale `[a2,a3,a4,a6]`. Entity names and aliases are *short strings*, where small embedding models measurably anti-correlate | entity count > ~150-200, or alias lookups start missing (count AMBIGUOUS/no-match events) |
| an LLM "pager" that reads pages and returns a slice | inserts a distillation step, and distillation dropping the load-bearing qualifier is the failure this design exists to stop. A deterministic script that resolves the alias and prints the read set does the same job with no drift | the deterministic version measurably fails |
| a graph/KG layer | `depends:`/`dependents:` answer multi-hop at this scale `[a5]` | queries those two columns cannot serve |

**Where embeddings *do* earn their place: the lint, not the retrieval** — near-duplicate detection
over wiki *paragraphs* (prose-length, where they measurably work) to find the same story told in four
places. On demand, never in the read path.

## 13. Enforcement, because none of the above self-executes

`SYNTHESIS.md` §1: the two benchmarks that test *obedience* rather than recall found the governing
document was **never opened in ~96-97% of violations**, even one grep away `[a7]`; compaction takes
rule violation from 0% to 30-59% `[a9]`; deterministic out-of-band gates block >90% of unsafe
executions at millisecond cost `[a9]`.

0. **A loader.** Nothing is "always loaded" because a design says so — a hook has to put it there, on
   `SessionStart` **and** `PostCompact`. This is easy to miss precisely because everything around it
   looks finished: the surfaces generate, the gate blocks edits, and the index is still absent from
   context. **BUILT** as `~/.claude/hooks/load-wiki.ps1` — regenerates first, reports lint
   inline, ~19k tokens for one project's wiki, `$env:WIKI_LOAD='off'` to disarm.
1. **Size caps** — removes the incentive to skim. Free.
2. **Read receipt** — before proposing, name the entries that govern the change. A grep cannot fake
   it: it names lines, not decisions. Free.
3. **A hook gate** — `PreToolUse` on edit/write: was the owning entity's file read this session? The
   file→entity map it needs is the `owns:` line. **BUILT** as
   `~/.claude/hooks/guard-entity-read.ps1` (+ `~/.claude/hooks/test-entity-read.ps1`, 9/9 passing).
   Ownership from `owns:`, proof-of-reading from the session transcript, permissive at every edge,
   disarm with `$env:WIKI_GATE='off'`. It is ~90 lines and needed no new registry — which is the
   payoff of putting `owns:` in the header in the first place.

---

## Applying this to another project

1. **Inventory first, generated from the code** — entities, with `dependents:` derived from imports.
   Do not author the dependency graph.
2. **Name registry second** — canonical names, aliases, ambiguity rows. This alone fixes "one word,
   six things" and costs an hour.
3. **Extract before you move anything.** The considerations live in transcripts and logs; moving the
   files first loses them. Extraction is targeted per entity, newest-first, and **stops at
   saturation** — the bar is that a reader can answer *does it exist / was it tried / what breaks /
   is the reason still true* without opening a transcript.
4. **Only then** restructure pages, split the decision ledger, and move history out.
5. **Adopt the caps on day one.** Everything else degrades gracefully; an uncapped always-loaded
   layer regrows the original problem.
