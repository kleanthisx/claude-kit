# kind:namespace/name
aka:         the name people use - another name - the file name
state:       LIVE - what this is and what is true about it NOW, in one or two sentences  ->  planned: where it is going (or -)
owns:        path/to/file.py - path/to/folder/ - `path with spaces/file.txt`
depends:     kind:namespace/other-page - kind:namespace/another-page
dependents:  -
invariants:  what must not change, and what breaks if it does
open:        known defects and gaps right now (or -)
verified:    YYYY-MM-DD - what was read or run to check this page
index:       What it is - How it works - Design - Decisions - Dead ends - Open - Change log

## What it is

One paragraph: what this thing is and where it sits.

## How it works

The steps, the data and the knobs, with `file:line` locators.

## Design

The fundamental parts and the reason for each. Where no reason is recorded, ask; never invent one.

## Decisions

**example-decision-name** — STANDING ⚖ — what was decided and why. Evidence: path/to/evidence or the command run.

## Dead ends

**example-dead-end** — DISCARDED ✗ — what was tried, what happened, why it lost, what to do instead. Evidence: path.

## Open

Detail behind the open: line.

## Change log

- YYYY-MM-DD - page created. (When this grows, move it to archive/<page-stem>-history.md and link that file here.)
