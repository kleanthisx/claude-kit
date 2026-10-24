"""PreToolUse gate for THE COMMISSAR (~/.claude/commissar/). Code only, no model call; ~10 ms when she is up.

- mcp__commissar__* calls: register the call (hash of its arguments) with this session's id and transcript, so
  the service reads the operator's words itself. Then let the call through.
- Edit / Write / NotebookEdit / Bash / PowerShell: ask the service (/check). In enforce mode a "deny" stops the
  call, with the reason for the agent. In log mode it only records what it would do.
- Service down: log mode lets everything through; enforce mode fails closed - only read-only lines, scratch-only
  work and the command that starts the service pass.
"""
import hashlib
import json
import os
import sys
import urllib.request

COMMISSAR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "commissar")   # <ClaudeHome>/commissar, beside hooks/
URL = "http://127.0.0.1:8791"
START = f"python -I {COMMISSAR.replace(os.sep, '/')}/up.py"
ALWAYS = {START, f"python -I {COMMISSAR.replace(os.sep, '/')}/talk.py"}   # starting her, the /commissar relay


def post(path, body, timeout=10):
    req = urllib.request.Request(URL + path, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": "COMMISSAR: " + reason}}))


def mode():
    try:
        return json.load(open(os.path.join(COMMISSAR, "config.json"), encoding="utf-8")).get("mode", "log")
    except (OSError, ValueError):
        return "log"


def main():
    try:
        d = json.load(sys.stdin)
    except ValueError:
        return 0
    tool, ti = d.get("tool_name", ""), d.get("tool_input") or {}
    sid, tr, cwd = d.get("session_id", ""), d.get("transcript_path", ""), d.get("cwd", "")
    if tool.startswith("mcp__commissar__"):
        k = hashlib.sha256(json.dumps(ti, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                           .encode("utf-8")).hexdigest()
        try:
            post("/register", {"key": k, "session": sid, "transcript": tr})
        except OSError:
            pass                                       # the MCP call itself reports that she is down
        return 0
    if tool not in ("Edit", "Write", "NotebookEdit", "Bash", "PowerShell"):
        return 0
    try:
        r = post("/check", {"session": sid, "transcript": tr, "tool": tool, "input": ti, "cwd": cwd})
    except OSError:
        if mode() != "enforce":
            return 0
        sys.path.insert(0, COMMISSAR)
        from classify import classify
        cmd = ti.get("command", "")
        if tool in ("Bash", "PowerShell") and (cmd.strip().lower() in {a.lower() for a in ALWAYS} or classify(tool, cmd)["kind"] == "read-only"):
            return 0
        tmp = os.path.normcase(os.path.join(os.environ.get("TEMP", ""), "claude"))
        target = ti.get("file_path") or ti.get("notebook_path") or ""
        if target and os.path.normcase(os.path.abspath(target)).startswith(tmp):
            return 0
        deny(f"the commissar is not running, so nothing that changes state may run. Start her: {START}")
        return 0
    if r.get("decision") == "deny":
        deny(r.get("reason", "denied"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
