#!/usr/bin/env python3
"""Wiki generators + linter.

Reads every entity file's header and writes the generated surfaces. Nothing they contain is
hand-editable: the entity files are the single source of truth.

    python docs/wiki/generate.py                    # write OVERVIEW, DECISIONS, DISCARDED, NAMES
    python docs/wiki/generate.py --lint             # validate only, exit 1 on error
    python docs/wiki/generate.py --fix-dependents   # rewrite every dependents: line from the depends: lines

The default run writes the surfaces even when lint finds errors, and exits 0; --lint is the pass/fail check
(exit 1 on any error). On macOS and Linux the command is usually python3.

Layout it expects, next to this file:
    entities/*.md                 one page per thing (header format in WIKI-PRIMER.md)
    ledgers/*.md                  optional: measurement/record pages, same header
    archive/<stem>-history.md     optional: a page's moved-out history, still scanned for entries

Design and rules: WIKI-PRIMER.md. Written for Python 3.8+, standard library only; tested on 3.10, 3.12, 3.14.
"""
import re, sys, pathlib, collections, datetime

WIKI = pathlib.Path(__file__).resolve().parent
ENT = WIKI / "entities"
LEDG = WIKI / "ledgers"

CORE = ["aka", "state", "owns", "depends", "dependents", "invariants", "open", "verified", "index"]
OPTIONAL = ["run", "source", "produces", "params", "compat"]
# Caps apply ONLY to the generated surfaces, which are loaded at every session start: there, size is a
# cost paid every time. Entity pages have no size cap: a page is as big as the information it must hold,
# and is split only when it holds more than one thing. Only the operator changes a cap; a breach is
# reported, never silenced.
CAP_OVERVIEW = 160 * 1024     # always loaded
CAP_DECISIONS = 100 * 1024    # on demand
CAP_MAP = 25 * 1024           # DISCARDED.md, always loaded
CAP_NAMES = 80 * 1024         # always loaded
TRUST_DAYS = 14               # a verified: date older than this is flagged

NAME_RE = re.compile(r"^#\s*([a-z]+:[a-z0-9-]+/[a-z0-9-]+)\s*$", re.M)
# The always-loaded overview carries these header fields per entity; every other field is read in the
# entity file, on demand.
OVERVIEW_FIELDS = ["aka", "state", "verified"]
FIELD_RE = re.compile(r"^([a-z]+):\s{1,}(.*)$")
# a dead end or open question in a body: **name** - DISCARDED ... / **name** - OPEN ? ...
DISC_RE = re.compile(r"^\*\*([a-z0-9-]+)\*\*\s*[-—]\s*(DISCARDED[^\n]*|OPEN \?[^\n]*)", re.M)
REF_RE = None   # built in load() from the kinds actually present, so any domain's kinds work
ANY_REF = re.compile(r"\b[a-z]+:[a-z0-9-]+/[a-z0-9-]+")   # any kind: for depends:/dependents:, where a typo must show
CODE_SPAN = re.compile(r"`[^`\n]*`")                       # text in backticks is not a page reference
ENTRY_END = re.compile(r"\n[ \t]*\n|\n#|\n\*\*")           # an entry ends at a blank line, a heading or the next entry


def cell(s):
    """Text for a markdown table cell: a | would split the row."""
    return s.replace("|", "\\|")


def write(path, text):
    # open() rather than Path.write_text(newline=...), which needs Python 3.10
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def parse(path):
    txt = path.read_text(encoding="utf-8")
    m = NAME_RE.search(txt)
    name = m.group(1) if m else None
    fields, order = {}, []
    for line in txt.splitlines()[1:]:
        if line.startswith("#"):
            break
        fm = FIELD_RE.match(line)
        if fm:
            fields[fm.group(1)] = fm.group(2).strip()
            order.append(fm.group(1))
        elif line.strip() == "":
            if fields:
                break
    return {"path": path, "name": name, "fields": fields, "order": order,
            "text": txt, "size": len(txt.encode("utf-8"))}


def load():
    global REF_RE
    ents = [parse(p) for p in sorted(list(ENT.glob("*.md")) + list(LEDG.glob("*.md")))]
    # A page's history file (archive/<stem>-history.md, linked from the page) still holds named entries:
    # superseded decisions and dead ends stay in DECISIONS.md and the map. An inaccessible record does not
    # exist.
    for e in ents:
        h = WIKI / "archive" / f"{e['path'].stem}-history.md"
        e["htext"] = h.read_text(encoding="utf-8") if h.exists() else ""
    kinds = sorted({e["name"].split(":")[0] for e in ents if e["name"]}) or ["entity"]
    REF_RE = re.compile(r"\b(?:" + "|".join(map(re.escape, kinds)) + r"):[a-z0-9-]+/[a-z0-9-]+")
    return ents


def dependents_check(e, ents):
    """(derived, authored, ok): derived = the reverse of every depends: line; ok when the dependents: line
    names exactly those pages, and holds no other text when there are none."""
    derived = sorted({o["name"] for o in ents if o["name"] and o is not e
                      and e["name"] in set(REF_RE.findall(o["fields"].get("depends", "")))})
    line = e["fields"].get("dependents", "").strip()
    authored = sorted(set(REF_RE.findall(line)))
    empty_mark = line in ("-", "—", "–") or line.startswith("none")
    ok = derived == authored and (bool(derived) or empty_mark)
    return derived, authored, ok


def lint(ents):
    errs, warns = [], []
    have = {e["name"] for e in ents if e["name"]}
    for e in ents:
        n = e["name"] or e["path"].name
        if not e["name"]:
            errs.append(f"{e['path'].name}: first line is not '# kind:namespace/name'")
            continue
        for f in CORE:
            if f not in e["fields"]:
                errs.append(f"{n}: missing mandatory field '{f}:'")
            elif not e["fields"][f]:
                errs.append(f"{n}: field '{f}:' is empty - write an em dash, never omit")
        header_refs = set(ANY_REF.findall(e["fields"].get("depends", "") + " " + e["fields"].get("dependents", "")))
        for ref in sorted(header_refs - have):
            errs.append(f"{n}: depends:/dependents: names no page -> {ref} (unknown kind or a typo?)")
        for ref in sorted(set(REF_RE.findall(CODE_SPAN.sub(" ", e["text"]))) - have - header_refs):
            errs.append(f"{n}: dangling reference -> {ref}")
        # dependents: are GENERATED: the reverse of every depends: line. An authored line that disagrees
        # is reported; --fix-dependents rewrites it.
        derived, authored, ok = dependents_check(e, ents)
        if not ok:
            miss = sorted(set(derived) - set(authored))
            extra = sorted(set(authored) - set(derived))
            warns.append(f"{n}: dependents: disagrees with the depends: lines"
                         + (f" - missing {', '.join(miss)}" if miss else "")
                         + (f" - not a user {', '.join(extra)}" if extra else "")
                         + ("" if miss or extra else " - holds text but no page uses this one")
                         + " (run --fix-dependents)")
        v = e["fields"].get("verified", "")
        dm = re.search(r"(\d{4})-(\d{2})-(\d{2})", v)
        if dm:
            d = datetime.date(*map(int, dm.groups()))
            age = (datetime.date.today() - d).days
            if age > TRUST_DAYS:
                warns.append(f"{n}: verified {age} days ago - past the two-week trust horizon")
        else:
            warns.append(f"{n}: verified: carries no date")
    return errs, warns


def overview(ents):
    out = ["# OVERVIEW - every entity in this project",
           "",
           "> **GENERATED by `generate.py` - do not edit.** The entity files under `entities/` are the",
           "> source of truth. Each row carries name, aka, state and verified; owns, depends, dependents,",
           "> invariants, open and run are in the entity file.",
           f"> Generated {datetime.date.today().isoformat()} from {len(ents)} entities.",
           "",
           "Completeness is the point: if a thing exists in this project it has a row here, so nothing",
           "can be rebuilt by accident. Detail lives in the entity file, on demand.",
           ""]
    by_kind = collections.defaultdict(list)
    for e in ents:
        if e["name"]:
            by_kind[e["name"].split(":")[0]].append(e)
    for kind in sorted(by_kind):
        out.append(f"## {kind}")
        out.append("")
        for e in sorted(by_kind[kind], key=lambda x: x["name"]):
            f = e["fields"]
            folder = e["path"].parent.name
            out.append(f"### {e['name']}   ·   [{e['path'].name}]({folder}/{e['path'].name})")
            for k in e["order"]:
                if k in OVERVIEW_FIELDS:
                    out.append(f"- **{k}:** {f[k]}")
            out.append("")
    return "\n".join(out)


def discarded(ents):
    rows = []
    for e in ents:
        # entries in the page's history file stay on the map, tagged: superseded, not current
        for text, tag in ((e["text"], ""), (e["htext"], " (archived)")):
            for m in DISC_RE.finditer(text):
                nm, status = m.group(1), m.group(2).strip()
                word, _, rest = status.partition(" ")
                # what happened = the rest of the entry's first line, then the lines after it
                # stop at the entry's end: a blank line, a heading or the next entry
                tail = rest + " " + ENTRY_END.split(text[m.end(): m.end() + 400])[0]
                tail = re.sub(r"\s+", " ", tail).strip(" -—?✓✗⚖")
                rows.append((e["name"], nm, word + tag, cell(tail[:200])))
    out = ["# THE MAP - every dead end and open question in this project",
           "",
           "> **GENERATED by `generate.py` - do not edit.** Concatenated from the `DISCARDED`/`OPEN`",
           "> entries in every entity body.",
           ">",
           "> **Read this before proposing anything.** You cannot search for a decision whose name you do",
           "> not know, so this is pushed into the read set rather than waited for.",
           f"> Generated {datetime.date.today().isoformat()} - {len(rows)} entries.",
           "",
           "| entity | name | status | what happened |",
           "|---|---|---|---|"]
    for ent, nm, st, tail in sorted(rows):
        out.append(f"| `{ent}` | **{nm}** | {st} | {tail} |")
    return "\n".join(out)


def names(ents):
    alias = collections.defaultdict(list)
    for e in ents:
        if not e["name"]:
            continue
        alias[e["name"].lower()].append(e["name"])
        raw = e["fields"].get("aka", "")
        for a in re.split(r"[·|]|\s-\s", raw):
            a = a.strip().strip('"').strip("'").lower()
            if a and len(a) > 2:
                alias[a].append(e["name"])
    out = ["# NAMES - say this, mean that",
           "",
           "> **GENERATED by `generate.py` - do not edit.** Built from every entity's `aka:` line.",
           "> Canonical form is `kind:namespace/name`; aliases resolve to it.",
           "> **A row marked AMBIGUOUS means ASK, never guess.**",
           f"> Generated {datetime.date.today().isoformat()}.",
           "",
           "| you say | it means |",
           "|---|---|"]
    amb = 0
    for a in sorted(alias):
        targets = sorted(set(alias[a]))
        if len(targets) > 1:
            amb += 1
            out.append(f"| **{a}** | **AMBIGUOUS - ask.** " + " · ".join(f"`{t}`" for t in targets) + " |")
        else:
            out.append(f"| {a} | `{targets[0]}` |")
    out.insert(6, f"> {len(alias)} names, **{amb} ambiguous**.")
    return "\n".join(out)


DEC_RE = re.compile(r"^\*\*([a-z][a-z0-9]*(?:-[a-z0-9]+)+)\*\*\s*[-—]\s*"
                    # [ \t]* not \s*: a status at the end of its line must not reach into the next line
                    r"(PROVEN|DISCARDED|STANDING|OPEN)[ \t]*[✓✗⚖?]?[ \t]*[-—]?[ \t]*"
                    # the gist stops at the entry's end (blank line, heading, next entry), so a short
                    # entry does not swallow the section after it
                    r"((?:(?!\n[ \t]*\n|\n#|\n\*\*).){0,150})",
                    re.M | re.S)


def decisions(ents):
    rows = []
    for e in ents:
        # entries in the page's history file are listed, tagged: superseded or moved out, not in force
        for text, tag in ((e["text"], ""), (e["htext"], " (archived)")):
            for m in DEC_RE.finditer(text):
                gist = re.sub(r"\s+", " ", m.group(3)).strip()
                rows.append((e["name"], m.group(1), m.group(2) + tag, cell(gist[:130])))
    out = ["# DECISIONS - the one-line ledger",
           "",
           "> **GENERATED by `generate.py` - do not edit.** One line per durable decision, built from the",
           "> entity bodies that own them. The full entry, with its evidence, is in the entity.",
           "> Loaded ON DEMAND: grep it for a decision by name.",
           f"> {len(rows)} decisions across {len({r[0] for r in rows})} entities.",
           "",
           "| status | decision | entity | gist |",
           "|---|---|---|---|"]
    order = {"PROVEN": 0, "STANDING": 1, "OPEN": 2, "DISCARDED": 3}
    for ent, nm, st, gist in sorted(rows, key=lambda r: (r[2].endswith("(archived)"), order.get(r[2].split(" ")[0], 9), r[0], r[1])):
        out.append(f"| {st} | **{nm}** | `{ent}` | {gist} |")
    return "\n".join(out)


def fix_dependents(ents):
    """Rewrite every dependents: line as the reverse of all depends: lines (dependents are generated,
    never authored). Each replaced line is kept, verbatim, in ../history/dependents-lines-replaced.md,
    so no hand-written note becomes unreachable."""
    today = datetime.date.today().isoformat()
    kept = []
    for e in ents:
        if not e["name"]:
            continue
        derived, _, ok = dependents_check(e, ents)
        if ok:
            continue
        value = (" - ".join(derived) if derived else "none") + f" (generated from the depends: lines, {today})"
        lines = e["text"].split("\n")
        for i, line in enumerate(lines[:16]):
            m = re.match(r"^dependents:(\s+)(.*)$", line)
            if m:
                kept.append(f"- `{e['name']}` ({e['path'].name}), replaced {today}:\n  `{m.group(2)}`")
                lines[i] = f"dependents:{m.group(1)}{value}"
                write(e["path"], "\n".join(lines))
                break
    if kept:
        hist = WIKI.parent / "history" / "dependents-lines-replaced.md"
        hist.parent.mkdir(parents=True, exist_ok=True)
        head = "" if hist.exists() else ("# dependents: lines replaced by `generate.py --fix-dependents`\n\n"
                                         "Each line as it stood before it was regenerated from the depends: lines.\n\n")
        with open(hist, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(head + "\n".join(kept) + "\n")
    print(f"--fix-dependents: {len(kept)} dependents: lines rewritten")


def main():
    ents = load()
    if not ents:
        print("no entity files found in", ENT)
        return 1
    if "--fix-dependents" in sys.argv:
        fix_dependents(ents)
        ents = load()
    errs, warns = lint(ents)
    for w in warns:
        print("WARN ", w)
    for e in errs:
        print("ERROR", e)
    if "--lint" in sys.argv:
        print(f"\n{len(ents)} entities, {len(errs)} errors, {len(warns)} warnings")
        return 1 if errs else 0

    for fname, text, cap in (("OVERVIEW.md", overview(ents), CAP_OVERVIEW),
                             ("DECISIONS.md", decisions(ents), CAP_DECISIONS),
                             ("DISCARDED.md", discarded(ents), CAP_MAP),
                             ("NAMES.md", names(ents), CAP_NAMES)):
        write(WIKI / fname, text)
        size = len(text.encode("utf-8"))
        flag = "  ** OVER CAP - report it **" if size > cap else ""
        print(f"wrote {fname:14} {size:7,} bytes  (~{size//4:,} tokens, cap {cap//1024} KB){flag}")
    print(f"\n{len(ents)} entities, {len(errs)} errors, {len(warns)} warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
