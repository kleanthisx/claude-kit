#!/usr/bin/env python3
"""Render a Claude Code session transcript (.jsonl) into a log a human can read.

The transcript already exists -- Claude Code writes every session to
    <CLAUDE_HOME>/projects/<encoded-cwd>/<session-uuid>.jsonl
(CLAUDE_HOME defaults to ~/.claude) with full tool calls and results. It is JSON, so nobody reads
it. This turns one into markdown: what was asked, what was done, what came back, and what the Stop
hook (if one is wired) said about it.

Why it exists: the work log must be a record of the WORK -- including the
mistakes -- and must outlive the session. A subagent scribe writing prose from
memory is a second, lossy copy of something already on disk exactly.

    python render_session.py                         # newest session for the CURRENT cwd, writes ./session-<date>-<id>.md
    python render_session.py --session d81aaa55       # id or prefix
    python render_session.py --list                   # what is available
    python render_session.py --out docs/wiki/sessions/today.md
    python render_session.py --thinking --full        # everything, untruncated
    python render_session.py --project C--path-to-some-other-project   # a project other than the cwd's
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
CLAUDE_HOME = os.environ.get("CLAUDE_HOME") or os.path.join(HOME, ".claude")
PROJECTS = os.path.join(CLAUDE_HOME, "projects")
ANSI = re.compile(r"\x1b\[[0-9;]*m")
# Injected context blocks: real, but they are machinery, not what a person did.
NOISE = re.compile(
    r"<system-reminder>.*?</system-reminder>"
    r"|<local-command-caveat>.*?</local-command-caveat>"
    r"|<command-name>.*?</command-name>"
    r"|<command-message>.*?</command-message>"
    r"|<command-args>.*?</command-args>"
    r"|<local-command-stdout>.*?</local-command-stdout>",
    re.S,
)


def encode_project_dir(path):
    """Mirror Claude Code's own project-dir encoding: every character that is not a letter or
    digit becomes one literal '-' (no collapsing). 'C:\\Users\\you\\projects' ->
    'C--Users-you--projects'. Used only to compute a DEFAULT when --project is not given --
    never hardcode a specific encoded name here, it is different on every machine and account."""
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def clean(s):
    if not isinstance(s, str):
        return ""
    return ANSI.sub("", NOISE.sub("", s)).strip()


def deheading(s):
    """Escape markdown headings that came from QUOTED CONTENT (a file we read, a log we pasted).
    Unescaped, they join this document's own outline: a `## [2026-09-16] method + corpus` line from
    log.md rendered as a top-level turn heading and broke the structure."""
    return re.sub(r"(?m)^(#{1,6})(\s)", r"\\\1\2", s or "")


def clip(s, n):
    s = (s or "").strip()
    if n <= 0 or len(s) <= n:
        return s
    return s[:n].rstrip() + "\n  ... [%d more chars]" % (len(s) - n)


def local(ts, fmt="%H:%M:%S"):
    """Transcript timestamps are UTC; a human reads local time. Used for BOTH the header and the
    entries -- printing the raw ISO string in one and the converted time in the other made the
    header disagree with its own body by the UTC offset."""
    if not ts:
        return ""
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime(fmt)
    except Exception:
        return ts[11:19] if len(ts) > 19 else ""


def hhmm(ts):
    return local(ts) or "     "


def tool_summary(name, inp):
    """One line naming what the call actually did -- the field that carries the intent."""
    if not isinstance(inp, dict):
        return name, ""
    for k in ("command", "file_path", "pattern", "path", "url", "prompt", "query", "skill", "to"):
        if inp.get(k):
            v = str(inp[k]).replace("\n", " ")
            return name, v
    return name, ""


def result_text(block):
    c = block.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(b.get("text", "") for b in c if isinstance(b, dict))
    return ""


def sessions_for(project_dir):
    return sorted(glob.glob(os.path.join(project_dir, "*.jsonl")), key=os.path.getmtime, reverse=True)


def render(path, args):
    out, meta = [], {"cwd": "", "branch": "", "models": set(), "start": "", "end": ""}
    pending = {}   # tool_use_id -> (name, summary)
    cost = None
    # A transcript can carry the same message twice (a replayed/queued record re-emits an earlier
    # turn near the end of the file), which rendered the session's FIRST turn again after its last
    # one. Dedupe on uuid: correct regardless of why the duplicate was written.
    seen = set()

    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        t, ts = d.get("type"), d.get("timestamp")
        if ts:
            meta["start"] = meta["start"] or ts
            meta["end"] = ts
        meta["cwd"] = d.get("cwd") or meta["cwd"]
        meta["branch"] = d.get("gitBranch") or meta["branch"]

        if t == "cost-state":
            cost = d
            continue

        if t == "system":
            for err in (d.get("hookErrors") or []):
                txt = clean(err)
                if txt:
                    out.append("\n> **[%s] HOOK — %s**\n>\n> %s\n"
                               % (hhmm(ts), (d.get("hookInfos") or [{}])[0].get("command", "hook"),
                                  clip(txt, args.max_result).replace("\n", "\n> ")))
            continue

        if t not in ("user", "assistant"):
            continue
        uid = d.get("uuid")
        if uid:
            if uid in seen:
                continue
            seen.add(uid)

        msg = d.get("message") or {}
        meta["models"].add(msg.get("model")) if msg.get("model") else None
        content = msg.get("content")

        if isinstance(content, str):
            txt = clean(content)
            if not txt:
                continue
            if txt.startswith("Stop hook feedback:"):
                out.append("\n> **[%s] STOP HOOK**\n>\n> %s\n"
                           % (hhmm(ts), clip(txt, args.max_result).replace("\n", "\n> ")))
            else:
                out.append("\n## [%s] YOU\n\n%s\n" % (hhmm(ts), deheading(clip(txt, args.max_user))))
            continue

        if not isinstance(content, list):
            continue

        for b in content:
            if not isinstance(b, dict):
                continue
            bt = b.get("type")
            if bt == "text":
                txt = clean(b.get("text"))
                if txt:
                    label = "CLAUDE" if t == "assistant" else "YOU"
                    out.append("\n### [%s] %s\n\n%s\n" % (hhmm(ts), label, deheading(clip(txt, args.max_text))))
            elif bt == "thinking" and args.thinking:
                txt = clean(b.get("thinking"))
                if txt:
                    out.append("\n<details><summary>[%s] thinking</summary>\n\n%s\n\n</details>\n"
                               % (hhmm(ts), clip(txt, args.max_text)))
            elif bt == "tool_use":
                name, summ = tool_summary(b.get("name", "?"), b.get("input"))
                pending[b.get("id")] = (name, summ)
                out.append("\n`[%s]` **→ %s** %s\n" % (hhmm(ts), name, "`%s`" % clip(summ, 300) if summ else ""))
            elif bt == "tool_result":
                name, _ = pending.pop(b.get("tool_use_id"), ("result", ""))
                txt = clean(result_text(b))
                if not txt:
                    continue
                err = " (ERROR)" if b.get("is_error") else ""
                out.append("```\n← %s%s\n%s\n```\n" % (name, err, clip(txt, args.max_result)))

    head = ["# Session log — %s" % os.path.basename(path).replace(".jsonl", ""),
            "",
            "| | |",
            "|---|---|",
            "| started | %s |" % (local(meta["start"], "%Y-%m-%d %H:%M:%S") or "?"),
            "| ended | %s |" % (local(meta["end"], "%Y-%m-%d %H:%M:%S") or "?"),
            "| cwd | `%s` |" % (meta["cwd"] or "?"),
            "| branch | %s |" % (meta["branch"] or "-"),
            "| model | %s |" % (", ".join(sorted(m for m in meta["models"] if m)) or "?")]
    if cost:
        head.append("| cost | $%.2f, %d lines added / %d removed |"
                    % (cost.get("totalCostUSD") or 0, cost.get("totalLinesAdded") or 0,
                       cost.get("totalLinesRemoved") or 0))
    head += ["", "_Rendered from the session transcript by `render_session.py`. "
                 "`YOU` = the operator, `CLAUDE` = the assistant, `→` = a tool call, `←` = what it "
                 "returned, `STOP HOOK` = a Stop-hook verdict on the turn above._", "", "---"]
    return "\n".join(head) + "\n" + "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="latest", help="session uuid or prefix, or 'latest'")
    ap.add_argument("--project", default="", help="encoded cwd dir under <CLAUDE_HOME>/projects "
                     "(default: computed from the CURRENT working directory, the same way Claude "
                     "Code encodes it)")
    ap.add_argument("--out", default="", help="output .md (default ./session-<date>-<id8>.md)")
    ap.add_argument("--list", action="store_true", help="list available sessions and exit")
    ap.add_argument("--thinking", action="store_true", help="include the assistant's thinking blocks")
    ap.add_argument("--full", action="store_true", help="no truncation anywhere")
    ap.add_argument("--max-text", type=int, default=4000)
    ap.add_argument("--max-user", type=int, default=4000)
    ap.add_argument("--max-result", type=int, default=800)
    a = ap.parse_args()
    if a.full:
        a.max_text = a.max_user = a.max_result = 0

    project = a.project or encode_project_dir(os.getcwd())
    pdir = os.path.join(PROJECTS, project)
    if not os.path.isdir(pdir):
        sys.exit("no such project dir: %s (looked under %s; pass --project to pick a different one, "
                  "or --list after cd'ing into the right directory)" % (pdir, PROJECTS))
    files = sessions_for(pdir)
    if not files:
        sys.exit("no sessions in %s" % pdir)

    if a.list:
        for f in files[:25]:
            print("%s  %8.1f KB  %s" % (dt.datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M"),
                                        os.path.getsize(f) / 1024.0, os.path.basename(f)[:-6]))
        return

    if a.session == "latest":
        path = files[0]
    else:
        match = [f for f in files if os.path.basename(f).startswith(a.session)]
        if not match:
            sys.exit("no session starting with %r (try --list)" % a.session)
        path = match[0]

    sid = os.path.basename(path)[:-6]
    out = a.out or "session-%s-%s.md" % (dt.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y%m%d"), sid[:8])
    d = os.path.dirname(os.path.abspath(out))
    if d and not os.path.isdir(d):
        os.makedirs(d)
    text = render(path, a)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote %s  (%.1f KB from %.1f KB of jsonl)"
          % (out, len(text.encode("utf-8")) / 1024.0, os.path.getsize(path) / 1024.0))


if __name__ == "__main__":
    main()
