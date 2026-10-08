#!/usr/bin/env python3
"""Ownership coverage: which project files does no wiki page own, and which owns: entries match nothing?

    python docs/wiki/coverage.py           # report; exit 1 if any file is unowned

Reads the owns: lines within the first 14 lines of every page in entities/ and ledgers/. An owns: entry is
a path relative to the project root: a file (`src/app.py`), a folder (`src/views/`), or a glob
(`scripts/*.sh`; only * and ? are wildcards).
Backtick-quote a path that contains spaces. Page names (kind:namespace/name) on the line are ignored.
The project's files come from git (tracked files plus new uncommitted ones, minus ignored ones), or from
a directory walk when it is not a git repository.
The wiki's own folders (docs/wiki/, docs/history/) count as owned. Deliberately unowned files are listed,
one pattern per line, in docs/wiki/coverage-ignore.txt ('#' starts a comment).
A bare word counts as a path when it contains '/', '\\', '.' or '*', or names a FILE at the project root
(Makefile); a folder needs its '/', so a prose word that happens to name a folder claims nothing. An entry
owns that exact file, everything under it when it is a folder (trailing / optional), or what it matches as
a glob; matching ignores case. A path with a :line locator is a citation and claims nothing. The same rule
is used by the kit's hooks/guard-entity-read.ps1.
Written for Python 3.8+, standard library only; tested on 3.10, 3.12, 3.14.
"""
import fnmatch, os, pathlib, re, subprocess, sys

WIKI = pathlib.Path(__file__).resolve().parent
ROOT = WIKI.parent.parent
PAGE_NAME = re.compile(r"\b[a-z]+:[a-z0-9-]+/[a-z0-9-]+")   # case-sensitive, as in the gate and generate.py
IMPLICIT = ["docs/wiki/", "docs/history/"]


def project_files():
    # tracked files plus new files not yet committed (minus ignored ones); -z and quotePath=false keep
    # non-ASCII names as they are instead of git's quoted octal escapes
    try:
        out = subprocess.run(["git", "-c", "core.quotePath=false", "ls-files", "-z", "--cached", "--others",
                              "--exclude-standard"],
                             cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
        files = sorted({f for f in out.split("\0") if f})
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    files = []
    for d, dirs, names in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in (".git", "__pycache__", "node_modules", ".venv")]
        for n in names:
            files.append(pathlib.Path(d, n).relative_to(ROOT).as_posix())
    return files


def owns_entries(text, root_files):
    """The owns: entries of a page as path patterns, step for step as hooks/guard-entity-read.ps1 does it:
    every owns: line within the page's first 14 lines; backtick-quoted paths taken whole first; then page
    names (kind:namespace/name) removed from the rest; a bare word counts as a path when it has a '/', '\\',
    '.' or '*' in it, or names a FILE at the project root (case ignored); other words are prose."""
    head = re.split(r"\r?\n|\r", text)[:14]   # line breaks as Get-Content counts them (not form feeds)
    value = " ".join(l for l in head if l.startswith("owns:"))
    if not value:
        return []
    value = re.sub(r"^owns:\s*", "", value)
    quoted = [q.strip() for q in re.findall(r"`([^`]+)`", value)]
    rest = PAGE_NAME.sub(" ", re.sub(r"`[^`]*`", " ", value))
    bare = []
    for w in re.split(r"\s+-\s+|[\s,;]+", rest):
        t = w.strip().strip("()").rstrip(".:").replace("\\", "/")
        if t and t != "-" and (re.search(r"[/.*]", t) or t.lower() in root_files):
            bare.append(t)
    out = []
    for p in quoted + bare:
        p = p.replace("\\", "/")
        if re.search(r":\d+(-\d+)?$", p):   # file:line is a citation, not a claim
            continue
        p = p[2:] if p.startswith("./") else p
        if p:
            out.append(p)
    return out


def matches(path, pat):
    """The same rule as hooks/guard-entity-read.ps1: the exact file, everything under a folder (trailing
    / optional), or a glob (only * and ? are wildcards; [ and ] are literal); case-insensitive. A bare
    name does not match at other depths."""
    path, pat = path.lower(), pat.lower()
    if "*" in pat or "?" in pat:
        return fnmatch.fnmatchcase(path, pat.replace("[", "[[]"))
    pat = pat.rstrip("/")
    return path == pat or path.startswith(pat + "/")


def main():
    pages = sorted(list((WIKI / "entities").glob("*.md")) + list((WIKI / "ledgers").glob("*.md")))
    root_files = {p.name.lower() for p in ROOT.iterdir() if p.is_file()}   # root FILES only; a folder needs its /
    owners = {}
    for p in pages:
        owners[p.name] = owns_entries(p.read_text(encoding="utf-8-sig"), root_files)
    ignore = list(IMPLICIT)
    ig = WIKI / "coverage-ignore.txt"
    if ig.exists():
        ignore += [l.split("#")[0].strip() for l in ig.read_text(encoding="utf-8").splitlines()
                   if l.split("#")[0].strip()]
    files = project_files()
    all_pats = [(page, pat) for page, pats in owners.items() for pat in pats]
    unowned = [f for f in files
               if not any(matches(f, pat) for _, pat in all_pats)
               and not any(matches(f, pat) for pat in ignore)]
    dead = [(page, pat) for page, pat in all_pats if not any(matches(f, pat) for f in files)]
    print(f"{len(files)} files, {len(pages)} pages, {len(all_pats)} owns: entries")
    print(f"unowned files: {len(unowned)}")
    for f in unowned:
        print("  UNOWNED", f)
    print(f"owns: entries that match no file: {len(dead)}")
    for page, pat in dead:
        print("  NO MATCH", page, "->", pat)
    return 1 if unowned else 0


if __name__ == "__main__":
    sys.exit(main())
