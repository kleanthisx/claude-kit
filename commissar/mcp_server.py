"""MCP server (stdio): the agent's side of the commissar. Two tools, both forwarded to service.py.

The call is matched to its Claude session by a key: the hash of the tool arguments. hooks/commissar-gate.py
sees the same call first (PreToolUse on mcp__commissar__*) and registers that key with the session id and
transcript path, so the service reads the operator's words from the transcript itself, never from the agent.
"""
import hashlib
import json
import sys
import urllib.error
import urllib.request

URL = "http://127.0.0.1:8791"

TOOLS = [
    {"name": "commissar_submit_plan",
     "description": ("Submit your plan to the commissar BEFORE acting. Required before any action that changes "
                     "state outside the session scratchpad; the gate denies such actions until a plan covering "
                     "them is approved, and again after every new message from the operator. She approves, "
                     "objects (answer with commissar_reply or revise and resubmit), or escalates to the operator "
                     "(then stop and put her question to the operator). List every file or folder the plan will "
                     "change and every state-changing command it will run; anything not listed is denied."),
     "inputSchema": {"type": "object", "properties": {
         "plan": {"type": "string", "description": "the steps, in order, and which of the operator's words each serves"},
         "stage": {"type": "string", "description": "which of the operator's three stages: get acquainted / draft 1 / work from there"},
         "cost": {"type": "string", "description": "worst-case cost and bound: tokens, time, operator interruptions"},
         "checklist": {"type": "array", "items": {"type": "string"}, "description": "the work as at most 6 items"},
         "assumptions": {"type": "array", "items": {"type": "string"}, "description": "every assumption, one line each"},
         "targets": {"type": "array", "items": {"type": "string"}, "description": "absolute paths of files/folders it will change"},
         "commands": {"type": "array", "items": {"type": "string"}, "description": "state-changing commands it will run (prefixes)"}},
         "required": ["plan", "stage", "cost", "checklist", "assumptions", "targets", "commands"]}},
    {"name": "commissar_reply",
     "description": "Answer the commissar's objection to your current plan. After 3 objections it goes to the operator.",
     "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
]


def key(args):
    return hashlib.sha256(json.dumps(args, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                          .encode("utf-8")).hexdigest()


def post(path, body, timeout=600):
    req = urllib.request.Request(URL + path, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def render(v):
    d = v.get("decision", "?")
    lines = [f"COMMISSAR: {d.upper()}", v.get("message", "")]
    if d == "escalate":
        lines.append("QUESTION FOR THE OPERATOR (stop and ask them): " + v.get("question_for_operator", ""))
    elif d == "object":
        lines.append("Revise the plan and resubmit, or answer with commissar_reply.")
    if v.get("rules_checked"):
        lines.append("Rules checked: " + "; ".join(v["rules_checked"]))
    return "\n".join(x for x in lines if x)


def call(name, args):
    if name == "commissar_submit_plan":
        v = post("/plan", {"key": key(args), **{f: args.get(f) for f in
                                                 ("plan", "stage", "cost", "checklist", "assumptions", "targets", "commands")}})
    elif name == "commissar_reply":
        v = post("/reply", {"key": key(args), "text": args.get("text", "")})
    else:
        raise ValueError(f"no tool {name}")
    if "error" in v:
        raise RuntimeError(v["error"])
    return render(v)


def main():
    for line in sys.stdin:
        try:
            m = json.loads(line)
        except ValueError:
            continue
        mid, method = m.get("id"), m.get("method")
        if mid is None:
            continue                                   # notifications (initialized, cancelled)
        try:
            if method == "initialize":
                res = {"protocolVersion": (m.get("params") or {}).get("protocolVersion", "2025-06-18"),
                       "capabilities": {"tools": {}}, "serverInfo": {"name": "commissar", "version": "0.1"}}
            elif method == "tools/list":
                res = {"tools": TOOLS}
            elif method == "tools/call":
                p = m.get("params") or {}
                try:
                    res = {"content": [{"type": "text", "text": call(p.get("name"), p.get("arguments") or {})}]}
                except (urllib.error.URLError, OSError) as e:
                    res = {"content": [{"type": "text", "text": f"COMMISSAR UNAVAILABLE: {e}"}], "isError": True}
                except Exception as e:  # noqa: BLE001
                    res = {"content": [{"type": "text", "text": f"COMMISSAR ERROR: {e}"}], "isError": True}
            elif method == "ping":
                res = {}
            else:
                out = {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"no method {method}"}}
                sys.stdout.write(json.dumps(out) + "\n"); sys.stdout.flush()
                continue
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid, "result": res}) + "\n")
            sys.stdout.flush()
        except Exception as e:  # noqa: BLE001
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid, "error": {"code": -32000, "message": str(e)}}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
