"""DEACTIVATED 2026-10-11 - kept as code, no longer registered in settings.json (operator: "deactivate it but not
remove from code. make a note in the file why it was deactivated").

Why: superseded by THE COMMISSAR (~/.claude/commissar/ + hooks/commissar-gate.py). This logger's verdicts were
wrong too often to use: on its first live session it would have asked before 11 of 13 calls (85%), from two
causes - a crude command classifier (read-only lines read as "cannot tell") and an intent test that matched
only file names in the operator's last message, so a bulk approval ("do them all") read as unrequested. The
classifier was rewritten as commissar/classify.py; the intent question went to the commissar, who reads the
operator's words and the agent's plan instead of file names. Its log, pre-action-log.jsonl, stays beside it.
To reactivate: add a PreToolUse entry for Edit|Write|NotebookEdit|Bash|PowerShell running
`python -I <ClaudeHome>/hooks/pre-action-log.py` (timeout 10) to ~/.claude/settings.json.

PreToolUse, SHADOW MODE: record what a pre-action check WOULD do, never block, print nothing.

Built 2026-10-10 after reading the Ekbasis paper and its Claude Code hook (claude-kit
docs/research/ekbasis-2026-10-10/). Their structure, our target: settle what plain code can settle, and
record the rest as "would ask". Their hook guards git work-loss in Bash; ours covers the class that went
wrong on 2026-10-10: Edit/Write on files the operator never named (a generator, the live startup hook,
memory files), and Bash/PowerShell lines that change state.

One JSON line per call to pre-action-log.jsonl beside this file: tool, target or command, the facts code
can read (git: in a repo, tracked, already dirty; a .bak sibling; the area: scratch / memory / harness /
repo / other), whether the operator's last message names the target, the verdict an asking gate would
give, and how long the check took. Review: python pre-action-review.py.

Never blocks: no stdout, exit 0, every error caught and logged. Disarm: env PRE_ACTION_LOG=off.
"""
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.environ.get("PRE_ACTION_LOG_FILE") or os.path.join(HERE, "pre-action-log.jsonl")
HOME = os.path.expanduser("~")
TEMP_CLAUDE = os.path.normcase(os.path.join(os.environ.get("TEMP", ""), "claude"))
CLAUDE_HOME = os.path.normcase(os.path.join(HOME, ".claude"))

# command names, format only (as Ekbasis' CHANGES_FILES does): what a line runs, not what it means
BASH_READ = {"ls", "cat", "head", "tail", "grep", "rg", "wc", "du", "df", "pwd", "which", "stat", "file", "sort",
             "uniq", "cut", "tr", "diff", "md5sum", "sha256sum", "echo", "printf", "true", "date", "cd", "env",
             "awk", "sed", "jq", "basename", "dirname", "realpath", "test", "["}
GIT_READ = {"status", "log", "diff", "show", "ls-files", "rev-parse", "blame", "branch", "tag", "remote",
            "describe", "cat-file", "ls-tree", "shortlog", "reflog", "check-ignore", "config"}
PS_READ_VERB = re.compile(r"^(get|select|test|measure|format|where|sort|convertfrom|convertto|out-string|"
                          r"write-host|write-output|group|compare|resolve|split-path|join-path)\b", re.I)
PS_CHANGE_VERB = re.compile(r"^(set|add|out-file|copy|move|remove|new|rename|clear|stop|start|restart|"
                            r"install|uninstall|expand|compress|invoke-webrequest)\b", re.I)
REDIRECT = re.compile(r"(?<![0-9&])>>?(?!\s*(/dev/null|\$null|&))")


def last_user_message(transcript):
    """The operator's last own words: the newest user entry with text, not a tool result."""
    try:
        size = os.path.getsize(transcript)
        with open(transcript, "rb") as fh:
            fh.seek(max(0, size - 768 * 1024))
            tail = fh.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return ""
    for line in reversed(tail):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        if o.get("type") != "user" or o.get("isMeta"):
            continue
        c = (o.get("message") or {}).get("content")
        if isinstance(c, str) and c.strip():
            return c
        if isinstance(c, list):
            texts = [x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text"]
            if texts and not any(isinstance(x, dict) and x.get("type") == "tool_result" for x in c):
                return "\n".join(texts)
    return ""


def git(args, cwd):
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=3)
        return r.returncode, r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return -1, ""


def area(path):
    p = os.path.normcase(os.path.abspath(path))
    if TEMP_CLAUDE and p.startswith(TEMP_CLAUDE):
        return "scratch"
    if p.startswith(os.path.join(CLAUDE_HOME, "projects")) and os.sep + "memory" + os.sep in p:
        return "memory"
    if p.startswith(CLAUDE_HOME):
        return "harness"
    return "other"


def file_facts(path):
    f = {"area": area(path), "exists": os.path.exists(path)}
    d = os.path.dirname(os.path.abspath(path))
    while d and not os.path.isdir(d):
        d = os.path.dirname(d)
    rc, root = git(["rev-parse", "--show-toplevel"], d) if d else (-1, "")
    f["in_git"] = rc == 0
    if rc == 0:
        if f["area"] == "other":
            f["area"] = "repo"
        rel = os.path.relpath(os.path.abspath(path), root)
        f["tracked"] = git(["ls-files", "--error-unmatch", "--", rel], root)[0] == 0
        f["dirty_before"] = bool(git(["status", "--porcelain", "--", rel], root)[1])
    base = os.path.basename(path)
    try:
        f["backup_sibling"] = any(n.startswith(base) and ".bak" in n for n in os.listdir(os.path.dirname(path) or "."))
    except OSError:
        f["backup_sibling"] = False
    return f


def named(path, msg):
    """Does the operator's last message name this file (basename, or basename without extension)?"""
    m = msg.lower()
    b = os.path.basename(path).lower()
    stem = os.path.splitext(b)[0]
    return bool(b and b in m) or (len(stem) >= 4 and stem in m)


def classify_command(tool, cmd):
    """read-only / changes / unknown, from the command names of each segment."""
    kinds = []
    for seg in re.split(r"\|\||&&|[;|\n]", cmd):
        words = seg.strip().split()
        while words and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]) or words[0] in ("&", "time")):
            words = words[1:]
        if not words or words[0].startswith("#") or words[0] in ("{", "}", "(", ")", "do", "done", "fi", "then"):
            continue
        w = words[0].strip("(\"'")
        if w.startswith("$") and len(words) > 2 and words[1] == "=":   # PowerShell: $x = <expression>
            w = words[2].strip("(\"'")
        elif re.fullmatch(r"\$[A-Za-z_][\w.]*", w) and len(words) == 1:  # PowerShell: $x.prop, a value printed
            kinds.append("read-only")
            continue
        name = os.path.basename(w).lower()
        if name in ("git", "git.exe"):
            sub = next((x for x in words[1:] if not x.startswith("-")), "")
            kinds.append("read-only" if sub in GIT_READ else "changes")
        elif tool == "PowerShell" and PS_READ_VERB.match(name):
            kinds.append("read-only")
        elif tool == "PowerShell" and PS_CHANGE_VERB.match(name):
            kinds.append("changes")
        elif name in BASH_READ and not (name == "sed" and re.search(r"\s-i", seg)):
            kinds.append("read-only")
        elif name in ("rm", "mv", "cp", "mkdir", "touch", "tee", "ln", "chmod", "rmdir", "tar", "unzip", "pip", "npm"):
            kinds.append("changes")
        else:
            kinds.append("unknown")
    if REDIRECT.search(re.sub(r"'[^']*'|\"[^\"]*\"", "", cmd)):
        kinds.append("changes")
    if not kinds or all(k == "read-only" for k in kinds):
        return "read-only"
    return "changes" if "changes" in kinds else "unknown"


def path_tokens(cmd):
    return re.findall(r"[A-Za-z]:[\\/][^\s\"';|]+|~?/[^\s\"';|]+", cmd)


def main():
    t0 = time.perf_counter()
    rec = {"t": time.strftime("%Y-%m-%dT%H:%M:%S")}
    try:
        if os.environ.get("PRE_ACTION_LOG") == "off":
            return 0
        data = json.load(sys.stdin)
        tool = data.get("tool_name", "")
        ti = data.get("tool_input") or {}
        msg = last_user_message(data.get("transcript_path") or "")
        rec.update(session=(data.get("session_id") or "")[:8], tool=tool, cwd=data.get("cwd"))
        reasons = []
        if tool in ("Edit", "Write", "NotebookEdit"):
            path = ti.get("file_path") or ti.get("notebook_path") or ""
            facts = file_facts(path)
            rec.update(target=path, facts=facts, named=named(path, msg))
            if facts["area"] == "scratch":
                verdict = "pass: scratch"
            elif rec["named"]:
                verdict = "pass: named in the operator's last message"
            else:
                reasons.append("the operator's last message does not name this file")
                if facts["area"] in ("memory", "harness"):
                    reasons.append(f"{facts['area']} file (no git)")
                elif not facts.get("in_git"):
                    reasons.append("outside git")
                if facts["exists"] and not facts.get("tracked") and not facts["backup_sibling"]:
                    reasons.append("an existing file with no git history and no backup")
                verdict = "would ask"
        elif tool in ("Bash", "PowerShell"):
            cmd = ti.get("command", "")
            kind = classify_command(tool, cmd)
            paths = path_tokens(cmd)
            rec.update(command=cmd[:500], kind=kind)
            if kind == "read-only":
                verdict = "pass: read-only"
            elif paths and all(area(p) == "scratch" for p in paths):
                verdict = "pass: scratch"
            else:
                reasons.append("the line changes state" if kind == "changes" else "code cannot tell what the line changes")
                verdict = "would ask"
        else:
            return 0
        rec.update(verdict=verdict, reasons=reasons, user_msg=msg[:600])
    except Exception as e:  # noqa: BLE001 - shadow mode never fails the call
        rec["error"] = f"{type(e).__name__}: {e}"
    rec["ms"] = round((time.perf_counter() - t0) * 1000)
    try:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
