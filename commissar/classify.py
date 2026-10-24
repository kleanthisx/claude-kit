"""What a Bash or PowerShell line does, by format only (command names, redirections, paths), for the gate.

Fixed 2026-10-11 against the four misreads in the shadow log of 2026-10-10 (a plain `cd`, string output,
ForEach-Object and friends, a `python -c` that only prints), all of which pre-action-log.py called
"cannot tell". Returns kind (read-only / changes), the paths the line names, whether it deletes, and
whether it reaches outside this machine.
"""
import os
import re

PS_READ = re.compile(r"^(get|select|where|foreach|sort|measure|format|out-string|out-host|write-host|write-output|"
                     r"test|join-path|split-path|resolve-path|convertto|convertfrom|compare|group|set-location|"
                     r"push-location|pop-location|start-sleep|import-csv|read-host)\b", re.I)
PS_DELETE = re.compile(r"^(remove-item|clear-content|clear-item)\b", re.I)
PS_CHANGE = re.compile(r"^(set|add|out-file|copy|move|remove|new|rename|clear|stop|start|restart|install|"
                       r"uninstall|expand|compress|export)\b", re.I)
PS_WEB = re.compile(r"^invoke-(webrequest|restmethod)\b", re.I)
KEYWORDS = {"if", "elseif", "else", "foreach", "for", "while", "until", "do", "try", "catch", "finally", "switch",
            "function", "param", "return", "exit", "break", "continue", "then", "fi", "done", "esac", "in"}
BASH_READ = {"ls", "cat", "head", "tail", "grep", "rg", "wc", "du", "df", "pwd", "which", "stat", "file", "sort",
             "uniq", "cut", "tr", "diff", "md5sum", "sha256sum", "echo", "printf", "true", "false", "date", "cd",
             "env", "awk", "jq", "basename", "dirname", "realpath", "test", "[", "nvidia-smi", "sleep", "type",
             "where", "dir", "findstr", "tasklist", "netstat", "whoami", "hostname", "readlink", "column", "less"}
BASH_DELETE = {"rm", "rmdir", "del", "erase", "rd", "shred", "unlink"}
BASH_CHANGE = {"mv", "cp", "mkdir", "touch", "tee", "ln", "chmod", "chown", "tar", "unzip", "pip", "pip3", "npm",
               "npx", "yarn", "winget", "choco", "taskkill", "kill", "dd", "rsync", "xcopy", "robocopy", "copy",
               "move", "ren", "rename", "patch", "install"}
GIT_READ = {"status", "log", "diff", "show", "ls-files", "rev-parse", "blame", "describe", "cat-file", "ls-tree",
            "shortlog", "reflog", "check-ignore", "grep", "help", "version", "--version", "show-ref", "for-each-ref",
            "merge-base", "count-objects", "fsck"}
GIT_READ_IF_LISTING = {"branch", "tag", "remote", "stash", "worktree", "config"}
GIT_DELETE = re.compile(r"\bgit\b.*\b(clean\b|checkout\s+--|restore\b|reset\s+--hard|stash\s+(drop|clear)|"
                        r"branch\s+-D\b|push\s+.*--force|push\s+-f\b)")
OUTWARD = re.compile(r"\bgit\b.*\bpush\b|\bgh\b\s+(pr|issue|repo|release|gist|api\s+-X\s*(POST|PATCH|PUT|DELETE))\b"
                     r"|\bcurl\b.*(-X\s*(POST|PUT|PATCH|DELETE)|--data|-d\s|-F\s)|\bnpm\s+publish|\btwine\s+upload",
                     re.I)
PY_WRITES = re.compile(r"open\([^)]*['\"][wax+]|\.write\(|\.write_text\(|\.write_bytes\(|os\.(remove|unlink|rename|"
                       r"replace|makedirs|mkdir|rmdir|system)|shutil\.|subprocess|\.unlink\(|\.mkdir\(|\.rename\(|"
                       r"json\.dump\(|to_csv\(|to_parquet\(|requests\.(post|put|delete|patch)|urlopen\(")
PATH_TOKEN = re.compile(r"[A-Za-z]:[\\/][^\s\"';|&<>(){}]*|~[\\/][^\s\"';|&<>(){}]*|"
                        r"(?<![\w$.-])(?:\.{1,2}[\\/])?[\w.-]+(?:[\\/][\w .-]+)+")


def _segments(line):
    """Split a command line into simple commands: on ; | && || newlines and braces/parens, outside quotes."""
    segs, cur, q, i = [], [], None, 0
    while i < len(line):
        ch = line[i]
        if q:
            cur.append(ch)
            if ch == q and line[i - 1:i] != "\\":
                q = None
        elif ch in "'\"":
            q = ch
            cur.append(ch)
        elif ch in ";|\n{}()" or line.startswith("&&", i):
            segs.append("".join(cur))
            cur = []
            if line.startswith("&&", i) or line.startswith("||", i):
                i += 1
        else:
            cur.append(ch)
        i += 1
    segs.append("".join(cur))
    return [s.strip() for s in segs if s.strip()]


def _strip_quoted(s):
    return re.sub(r"'[^']*'|\"[^\"]*\"", "''", s)


def _paths(tool, line):
    """Find path arguments, but not path-looking prose in PowerShell string expressions."""
    found = []
    for seg in _segments(line):
        scan = seg
        if tool == "PowerShell":
            words = seg.split()
            first = words[0].strip("\"'`").lower() if words else ""
            # These strings are values/output, not arguments naming files.  Keep strings assigned to a plain
            # variable: `$p = 'C:\\x'` is how PowerShell commands commonly name a real path later in the line.
            if (seg[:1] in "'\"" or first in ("write-output", "write-host", "echo") or
                    re.match(r"^\s*\$[\w:]+(?:\.[\w]+)+\s*=", seg)):
                scan = _strip_quoted(seg)
        found.extend(p.strip("\"'") for p in PATH_TOKEN.findall(scan))
    return [p for p in found if p and not p.startswith("-")]


def _python_kind(seg):
    m = re.search(r"\s-c\s+(\"(?:[^\"\\]|\\.)*\"|'[^']*')", seg)
    if m:
        return "changes" if PY_WRITES.search(m.group(1)) else "read-only"
    if re.search(r"\s-m\s+(pytest|json\.tool|pip\s+(list|show|freeze))\b", seg):
        return "read-only"
    return "changes"                       # a script: its effect is not visible in the line


def classify(tool, line):
    kinds, deletes, opaque = [], bool(GIT_DELETE.search(line)), False
    for seg in _segments(line):
        words = seg.split()
        while words and (words[0].lower() in KEYWORDS or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0])
                         or words[0] in ("&", "time", "@")):
            words = words[1:]
        if not words or words[0].startswith("#"):
            continue
        w = words[0].strip("\"'`")
        if seg[0] in "'\"" or re.fullmatch(r"-?\d+(\.\d+)?,?", w):  # a string (or "{0}" -f ...) or number printed
            kinds.append("read-only"); continue
        if w.startswith("$"):
            if len(words) > 2 and words[1] in ("=", "+="):                # $x = <expression>
                if words[2][0] in "'\"$@[(" or re.match(r"-?\d", words[2]):
                    kinds.append("read-only"); continue                    # a value, not a command
                words = words[2:]; w = words[0].strip("\"'`")
            elif re.fullmatch(r"\$[\w:.]+(\[[^\]]*\])?", w) and len(words) <= 3:
                kinds.append("read-only"); continue                        # $x / $x.prop printed
        if w[:1] in ("$", "[", "-", "@", ".", ",") or w in ("=", "+="):
            kinds.append("read-only"); continue          # an expression piece ((...).Content, $x, -flag), not a command
        name = os.path.basename(w).lower()
        if name.endswith(".exe"):
            name = name[:-4]
        if name == "git":
            rest = [x for x in words[1:] if not x.startswith("-")]
            if words[1:2] == ["-C"]:
                rest = [x for x in words[3:] if not x.startswith("-")]
            sub = rest[0] if rest else ""
            listing = sub in GIT_READ_IF_LISTING and not re.search(r"\s(-d|-D|-m|-M|--delete|add|remove|rm|drop|"
                                                                    r"pop|apply|push|clear|prune|--set|--unset)\b", seg)
            kinds.append("read-only" if sub in GIT_READ or listing or not sub else "changes")
        elif name in ("python", "python3", "py", "pythonw"):
            kinds.append(_python_kind(seg))
            opaque |= not bool(re.search(r"\s-(c|m)\s", seg))
        elif name in ("powershell", "pwsh"):
            m = re.search(r"-(?:Command|c)\s+(\"(?:[^\"\\]|\\.)*\"|'[^']*'|.+)$", seg, re.I)
            kinds.append(classify("PowerShell", m.group(1).strip("\"'"))["kind"] if m and not re.search(r"-File\b", seg, re.I)
                         else "changes")
            opaque |= bool(re.search(r"-File\b", seg, re.I))
        elif name == "find":
            kinds.append("changes" if re.search(r"\s-(delete|exec|execdir|ok)\b", seg) else "read-only")
        elif name == "read":
            kinds.append("read-only")
        elif tool == "PowerShell" and PS_WEB.match(name):
            kinds.append("changes" if re.search(r"-Method\s+['\"]?(Post|Put|Patch|Delete)|-OutFile", seg, re.I)
                         else "read-only")
        elif tool == "PowerShell" and PS_DELETE.match(name):
            kinds.append("changes"); deletes = True
        elif tool == "PowerShell" and PS_READ.match(name):
            kinds.append("read-only")
        elif tool == "PowerShell" and PS_CHANGE.match(name):
            kinds.append("changes")
        elif name in BASH_DELETE:
            kinds.append("changes"); deletes = True
        elif name in BASH_CHANGE:
            kinds.append("changes")
        elif name == "sed":
            kinds.append("changes" if re.search(r"\s-i", seg) else "read-only")
        elif name in BASH_READ:
            kinds.append("read-only")
        elif name in ("gh", "curl", "wget"):
            kinds.append("changes" if OUTWARD.search(seg) or re.search(r"\s-o\s|\s-O\b|--output", seg) else "read-only")
        else:
            kinds.append("changes")                                        # a program whose effect is not visible
            opaque = True
    bare = _strip_quoted(line)
    for m in re.finditer(r"(?<![0-9&<>])>>?\s*([^\s;|&]+)", bare):
        if m.group(1).lower() not in ("$null", "nul", "/dev/null") and not m.group(1).startswith("&"):
            kinds.append("changes")
    return {"kind": "changes" if "changes" in kinds else "read-only", "deletes": deletes,
            "outward": bool(OUTWARD.search(line)), "opaque": opaque, "paths": _paths(tool, line)}
