#!/usr/bin/env python3
"""Ownership coverage: which project files does no wiki page own, and which owns: entries match nothing?

    python docs/wiki/coverage.py           # report; exit 1 if any file is unowned

Reads the owns: line of every page in entities/ and ledgers/. An owns: entry is a path relative to the
project root: a file (`src/app.py`), a folder ending in / (`src/views/`), or a glob (`scripts/*.sh`).
Backtick-quote a path that contains spaces. Page names (kind:namespace/name) on the line are ignored.
The project's files come from git (tracked files plus new uncommitted ones, minus ignored ones), or from
a directory walk when it is not a git repository.
The wiki's own folders (docs/wiki/, docs/history/) count as owned. Deliberately unowned files are listed,
one pattern per line, in docs/wiki/coverage-ignore.txt ('#' starts a comment).
A bare word counts as a path when it contains '/', '.' or '*', or names something at the project root.
Written for Python 3.8+, standard library only; tested on 3.10, 3.12, 3.14.
"""
import fnmatch, os, pathlib, re, subprocess, sys

WIKI = pathlib.Path(__file__).resolve().parent
ROOT = WIKI.parent.parent
PAGE_NAME = re.compile(r"\b[a-z]+:[a-z0-9-]+/[a-z0-9-]+\b")
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


def owns_entries(text, root_names):
    """The owns: value of a page, split into path patterns. A bare word counts as a path when it has a '/',
    a '.' or a '*' in it, or names a file or folder at the project root (Makefile, LICENSE); other words
    on the line are prose and are skipped."""
    m = re.search(r"^owns:\s*(.*)$", text, re.M)
    if not m:
        return []
    value = PAGE_NAME.sub(" ", m.group(1))
    quoted = re.findall(r"`([^`]+)`", value)
    rest = re.sub(r"`[^`]+`", " ", value)
    bare = [t.strip(" ,;()") for t in re.split(r"\s+-\s+|[\s,;]+", rest)]
    pats = [q.strip() for q in quoted] + [t for t in bare if t and t != "-" and
                                          ("/" in t or "." in t or "*" in t or t in root_names)]
    return [p[2:] if p.startswith("./") else p for p in pats]


def matches(path, pat):
    if pat.endswith("/"):
        return path.startswith(pat)
    if any(c in pat for c in "*?["):
        return fnmatch.fnmatch(path, pat)
    return path == pat or path.startswith(pat.rstrip("/") + "/")


def main():
    pages = sorted(list((WIKI / "entities").glob("*.md")) + list((WIKI / "ledgers").glob("*.md")))
    root_names = {p.name for p in ROOT.iterdir()}
    owners = {}
    for p in pages:
        owners[p.name] = owns_entries(p.read_text(encoding="utf-8"), root_names)
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
