# Project wiki (paste these lines into the project's CLAUDE.md)

This project keeps its knowledge in `docs/wiki/`; the design is in `docs/wiki/WIKI-PRIMER.md`. The lines
below load the always-read surfaces when the session starts. They are generated: run
`python docs/wiki/generate.py` BEFORE starting the session, because the imports are read at launch. After a
compaction, re-read them.

@docs/wiki/OVERVIEW.md
@docs/wiki/NAMES.md
@docs/wiki/DISCARDED.md

Add one `@docs/wiki/doctrine/<file>.md` line here for each doctrine file the project has (method, testing,
hazards); doctrine is read whole every session.

Rules in force here (WIKI-PRIMER.md section 4):
- Resolve the operator's words through NAMES.md first; an AMBIGUOUS row means ask.
- Check DISCARDED.md before proposing anything.
- Before changing a file, read in full every page in docs/wiki/entities/ whose owns: line covers it, plus
  every page in their depends: and dependents: lines; name them and the entries that govern the change
  before proposing it.
- Update the owning page as the work happens. Never edit OVERVIEW, NAMES, DISCARDED or DECISIONS by hand.
- DECISIONS.md is on demand: grep it for a decision by name.
