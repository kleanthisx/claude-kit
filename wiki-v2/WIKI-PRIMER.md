# Wiki primer: how to build and keep the project wiki

For Claude and the operator. It describes the wiki design (wiki v2) with the operator's rulings, and how to
build one on an existing body of work. The generator `generate.py` and the coverage check `coverage.py` sit
beside this file; `entity-template.md` is a blank page. The reasons and sources behind the design are in
`DESIGN.md` and `SYNTHESIS.md`; they are older than this primer, and where they differ (no size cap on pages,
the cap values), this primer is current.

## 0. What the wiki is for

The wiki shows the state of things on entry and lets a session focus on what matters to the task at hand.
A page holds **what exists now, how it works, a short design spec with the reasons for its fundamental parts,
and the decisions in force.** A page is not a log.

It exists to stop four losses (the first cost the operator two days):

1. **Rebuilding what already exists.** A session that does not know a thing exists builds a second one. The
   worst case: a new feature is tested on a crude parallel copy of a pipeline built from scratch, which lacks
   the real pipeline's features and carries new bugs, and the feature "does not work" for days.
2. **Removing a fundamental part because its reason is not written down.** ("Here is a model call between
   the user and the bot; seems like a waste; remove it for speed.") Every fundamental part's page says why it
   is there.
3. **Re-deciding what was already decided**, or retrying a dead end, because nobody can search for a
   decision whose name they do not know.
4. **Digital archaeology.** A year later, "why does this exist?" should be answered by the page and the
   files it links, not by digging through years of version-control history.

## 1. Layout

```
docs/wiki/
  generate.py            generator + linter (Python 3.8+, standard library only)
  coverage.py            lists files no page owns
  coverage-ignore.txt    optional: files deliberately owned by no page, one pattern per line
  entities/              one page per thing                          authored
                         (keep entity-template.md OUTSIDE entities/: there it is linted as a page)
  ledgers/               optional: measurement tables, same header    authored
  archive/               <page-stem>-history.md, linked from the page authored
  doctrine/              how work is done here (method, testing, hazards)  authored, read wholesale
  TASKS.md               live tasks only                              authored
  IDEAS.md               might-do, unevaluated                        authored
  archive/TASKS-history.md   finished and dropped tasks, with date and evidence
  OVERVIEW.md  NAMES.md  DISCARDED.md  DECISIONS.md                  GENERATED - never edit
docs/history/            raw logs, transcripts, run output: never loaded, cited by path
```

Add the four generated files to `.gitignore`; they are rebuilt from the pages.

## 2. When each thing is read

The load classes are the design: decide **when** a thing is read, not only what it is about.

| class                                                            | read                                                          | cap      |
| ---------------------------------------------------------------- | ------------------------------------------------------------- | -------- |
| `OVERVIEW.md` - every page's name, aka, state, verified          | always, at session start                                      | 160 KB   |
| `NAMES.md` - every alias to its canonical page                   | always                                                        | 80 KB    |
| `DISCARDED.md` - every dead end and open question, one line each | always                                                        | 25 KB    |
| `doctrine/*.md` - method, testing, hazards                       | always, **wholesale**                                         | ~15 KB   |
| entity pages                                                     | on demand, by name; **in full** before changing what they own | **none** |
| `DECISIONS.md` - one line per durable decision                   | on demand (grep it)                                           | 100 KB   |
| ledgers, `TASKS.md`, `IDEAS.md`                                  | on demand                                                     | -        |
| `docs/history/`                                                  | never at orientation; cited by path                           | -        |

The caps are the operator's; only the operator changes one. They apply to what is loaded at every session
start (the generated surfaces, set in `generate.py`, and the doctrine, ~15 KB, which `generate.py` does not
measure), because that is paid for every time; entity pages have none. `generate.py` reports a breach; a breach goes in
`TASKS.md`, is never silenced, and is never fixed by trimming information out of a header.

**Doctrine cannot be routed.** It governs work on every page, and no task ever says "I am touching the
testing method", so it is read whole every session.

## 3. The page

### 3.1 The header

The first line is the canonical name; the fields follow, one per line, in this order:

```
# kind:namespace/name
aka:         every name a person might use for it, separated by " - "
state:       what is true NOW (one or two sentences)  ->  planned: where it is going
owns:        the files and folders this page is responsible for
depends:     the pages of the things it is made of or reads (kind:namespace/name, separated by " - ")
dependents:  GENERATED - the reverse of every depends: line (run generate.py --fix-dependents)
invariants:  what must not change, and what breaks if it does
open:        known defects and gaps right now
verified:    YYYY-MM-DD - what was read or run to check this page
index:       the body's section names
run:         (optional, runnable things only) the command that runs it
```

Field rules:

- **Empty is written `-` or an em dash, never omitted.** A missing field is a lint error.
- **`owns:`** lists paths relative to the project root. An entry owns that exact file, everything under it
  when it is a folder (trailing `/` optional), or what it matches as a glob (`*`, `?`); backtick-quote a
  path with spaces; backslashes count as `/`. A bare word counts as a path when it contains `/`, `.` or
  `*`, or names a FILE at the project root (`Makefile`); a folder needs its `/`, so a prose word that
  happens to name a folder claims nothing. A path with a `:line` locator is a citation and claims nothing.
  A bare name does not match at other depths: `README.md` owns the root README only. One file may be
  owned by several pages (a file that holds several components). Every file in the project is owned by at
  least one page; `coverage.py` lists the ones that are not, and `owns:` entries that match no file.
- **`depends:`** comes from evidence: an import, a file or table read, a call. Cite `file:line` in the body.
  A belief is not a dependency.
- **`dependents:`** is never authored. A hand-written dependency claim rots silently.
- **`state:`** opens with a one-word status (LIVE, PARTIAL, BROKEN, PLANNED, DONE, RETIRED) and carries the
  trajectory (`-> planned: ...`). Without it, the next session reads "X only" as the
  design and forks instead of adopting.
- **`verified:`** carries a date and the method. Older than two weeks = re-verify before relying on it; the
  linter warns.
- **Names:** `kind:namespace/name`, lowercase, words joined with `-`. Pick a small set of kinds for the
  domain (for example `app`, `component`, `pipeline`, `layer`, `data`, `tool`, `pass`, `ledger`) and
  namespaces for its areas. The generator accepts any kind that is used as a page name. A name on a
  `depends:` or `dependents:` line that matches no page (a typo, an unknown kind) is a lint error; in the
  body, a known-kind name that matches no page is an error too, except inside backticks.
- **`aka:`** feeds `NAMES.md`. A name that points to two pages is listed as **AMBIGUOUS: ask, never guess.**
  Remove an alias from the page it does not belong to.

### 3.2 The body

Order: header = reference (what is true now); body = explanation (how it works and why). Sections:

1. **What it is** - one paragraph.
2. **How it works** - the steps, the data, the knobs, with `file:line` locators.
3. **Design** - the fundamental parts and **the reason for each**. Where no reason is recorded, ask the
   operator; never invent one.
4. **Decisions** - entries (format below), the ones in force.
5. **Dead ends** - `DISCARDED` entries: what was tried, what happened, why it lost, what to do instead.
6. **Open** - detail behind the `open:` line.
7. **Change log** - short dated lines of what changed on the page. When it grows, move it to the history
   file.

**Entry format** (the generator builds `DECISIONS.md` and `DISCARDED.md` from these):

```
**kebab-case-name** — STATUS — what was decided and why. Evidence: <path, command or run>.
```

- `STATUS` is one of `PROVEN ✓`, `STANDING ⚖`, `OPEN ?`, `DISCARDED ✗`. The name needs at least one hyphen.
- **Never edit an accepted entry; supersede it** with a new entry that says `Supersedes: <name>`, and move
  the old one to the history file.
- `DISCARDED` means **tried and beaten**. An idea nobody evaluated is `OPEN`, not `DISCARDED`.
- Not every decision earns an entry: durable ones only.

### 3.3 History leaves the page, but stays reachable

A page holds the state, not the account of how it got there. Superseded entries, old change-log lines and
long run accounts move to `archive/<page-stem>-history.md`, **linked from the page**. Never move anything
only into version-control history or a commit message: an inaccessible record does not exist. The generator
still scans the history file: its entries stay in `DECISIONS.md` and on the map, with `(archived)` after the
status, so a superseded decision is never read as one in force.

## 4. The operator's rulings

1. **Correct wiki work follows the design.** Read this primer before reshaping the wiki.
2. **One page per thing.**
3. **A page is as big as the information it must hold.** It is split only when it holds MORE THAN ONE THING,
   never because of its size. What leaves a page is content about a different thing (to that thing's page)
   and history (to the linked history file).
4. **A page is not a log.** It says what exists now, how it works, the design and the reasons for its
   fundamental parts, the decisions in force and the dead ends.
5. **Composition is explicit.** A screen, feature or pipeline is an arrangement of basic components: its page
   lists them in `depends:`. Each component has ONE page that lists **every place the code implements it,
   copies included**. Parallel copies then cannot be missed, and new work is tested through the real
   pipeline, never through a rebuilt copy. (Example: a browse page is a menu, a search and filter bar and a
   grid of item tiles; a picker elsewhere that opens the same browser, filter and all, depends on the same
   component pages, and any second implementation is listed on them.)
6. **Before changing a thing, read in full every page that owns the file, plus every page named in their
   `depends:` and `dependents:` lines.** You cannot alter a pipeline without knowing how every part directly
   related to it works. Before proposing the change, name the pages read and the entries that govern it.
7. **Write in flight.** The page that owns the thing is updated at the moment of the work, as field updates
   (overwritten, bounded), never as appended narrative. There is no separate session log; the session
   transcript is the record of the account.
8. **Never hand-edit a generated surface.**
9. **Point at executable facts; never copy them.** If a launch script, an argument parser, a config or the
   version-control history already states a fact, the page points at it.
10. **Capture free-form; structure afterwards.** The operator writes an idea however it comes out; Claude adds
    the routing and the structure.
11. **`TASKS.md` holds live tasks only:** `- [ ] what - page - [date set]`. A finished or dropped task moves to
    `archive/TASKS-history.md` with its date and evidence or reason. `IDEAS.md` holds unevaluated ideas; a
    page's `open:` line holds the condition. Every idea and task eventually leaves: promoted, tried, done, or
    dropped with a reason.
12. **Measurements:** one ledger per measurement class, rows never deleted (the losers answer "has anyone
    tried X?"). Every row carries the configuration that produced it; two rows are comparable only on the
    same configuration.
13. **An example the operator gives illustrates a general rule.** Build the rule for every case it covers.

## 5. Building a wiki on existing work

Three stages. Show the operator the result of each stage before the next.

**Stage 1 - get acquainted (read-only).**

1. List every file: `git ls-files > inventory.txt` (or a full directory listing). Sort it by folder and read
   it whole. Do not sample.
2. Find the existing records: READMEs, design notes, decision lists, tickets, runbooks, run logs.
3. Write a one-line-per-thing candidate list: every application, screen, component, pipeline, data set,
   tool, script group, external system. Mark the ones that are copies of each other.

**Stage 2 - draft 1, complete in every aspect, rough everywhere.**

1. Choose the kinds and namespaces. Turn the candidate list into canonical names. Show the list to the
   operator before writing pages: renaming a list is cheap, renaming 80 pages is not.
2. Write **every** page's header from `entity-template.md`: aka, state, owns, depends (from imports, reads and
   calls), invariants, open, verified (today's date and what you read), index. Bodies can be one paragraph.
3. Run `python docs/wiki/coverage.py` until every file is owned, or listed as deliberately unowned in
   `coverage-ignore.txt`.
4. Run `python docs/wiki/generate.py --fix-dependents`, then `python docs/wiki/generate.py --lint` until it
   reports 0 errors. Resolve every AMBIGUOUS name, or ask.
5. Move the existing decision records into the pages that own them as entries, quoted verbatim with their
   source path. Move history into the history files, linked.
6. Check draft 1: lint 0 errors; coverage 0 unowned; `OVERVIEW.md` has a row for every item on the candidate
   list; three pages' `depends:` lines spot-checked against the code.

**Stage 3 - deepen each page when it is next touched.** Fill How it works, Design with its reasons, the
entries and the dead ends. Do it page by page as work reaches it, not as a bulk pass: a bulk rewrite is how a
load-bearing qualifier gets dropped.

## 6. The session routine

- **Enter** (read-only): regenerate (`generate.py`), read `OVERVIEW.md`, `NAMES.md`, `DISCARDED.md` and
  `doctrine/` if they are not already in context, read `TASKS.md`, resolve the operator's words to page names
  through `NAMES.md` (AMBIGUOUS = ask), check `git status`, report, and wait. Never open `docs/history/` at
  orientation.
- **Work:** read the read set (ruling 6) before a change; update the owning page as you go.
- **Wrap:** check that every change made this session is on its owning page (write any straggler); run
  `generate.py` and report errors, warnings and cap breaches; update `TASKS.md` (move finished and dropped
  tasks to the history file); propose a commit and wait for a yes.

The kit's `/enter` and `/wrap` skills (`skills/enter`, `skills/wrap`) do these steps in Claude Code.

## 7. Getting the surfaces into context

- **Claude Code:** put the lines from `PROJECT-CLAUDE.md` into the project's `CLAUDE.md`. Its `@` imports
  load the generated surfaces and the doctrine when the session starts, so run `generate.py` BEFORE starting
  the session; `/enter` regenerating later does not refresh what was already imported. `/enter` sees the
  imported surfaces in context and does not read them again. After a compaction, re-read them.
- **claude.ai:** upload `OVERVIEW.md`, `NAMES.md`, `DISCARDED.md` and the doctrine files as project files;
  regenerate and re-upload after the pages change. Upload or paste a page when the work reaches it.
- **With the full kit installed**, hooks enforce this: `load-wiki.ps1` re-injects the surfaces at session
  start and after every compaction, and `guard-entity-read.ps1` blocks an edit (Edit, Write, NotebookEdit) to
  a file until its whole read set (ruling 6) has complete, successful Reads of each page's current version
  this session (chunked reads add up). It reads `owns:` by the same rule as `coverage.py` (section 3.1),
  searches `entities/` and `ledgers/`, and looks for the header in a page's first 14 lines. It lets the edit
  through when no transcript is available to check, and it does not see edits made through the shell. Without the kit, ruling 6 is a rule Claude follows on its own: ask for the read receipt when it
  matters.
- **Commands:** `python` here means the Python 3 command; on macOS and Linux that is usually `python3`.
  `generate.py` writes the surfaces even when lint finds errors and exits 0; `generate.py --lint` is the
  pass/fail check.
