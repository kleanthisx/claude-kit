"""The /commissar relay: the operator speaks to her. Takes no arguments, deliberately: the service reads the
operator's words from this session's transcript (their last message must be the /commissar command), so the
agent running this script cannot put words in the operator's mouth or switch her off.

    python -I <ClaudeHome>/commissar/talk.py
"""
import glob
import json
import os
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
found = glob.glob(os.path.join(os.path.expanduser("~"), ".claude", "projects", "*", sid + ".jsonl")) if sid else []
if not found:
    print("THE COMMISSAR CANNOT FIND THIS SESSION (no CLAUDE_CODE_SESSION_ID or no transcript)")
    sys.exit(1)
req = urllib.request.Request("http://127.0.0.1:8791/talk", data=json.dumps({"session": sid, "transcript": found[0]}).encode(),
                             headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=600) as r:
        v = json.loads(r.read())
except urllib.error.HTTPError as e:                  # she is up and said no
    try:
        why = json.loads(e.read()).get("error", str(e))
    except ValueError:
        why = str(e)
    print(f"THE COMMISSAR REFUSED: {why}")
    sys.exit(1)
except OSError as e:                                   # she is not reachable
    print(f"THE COMMISSAR IS UNAVAILABLE ({e}). Start her: python -I {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'up.py')}")
    sys.exit(1)
if "control" in v:
    print(v["text"])
else:
    print(v.get("answer", ""))
    if v.get("doctrine_changed"):
        print("\n[she changed her copy of the method; the earlier version is in ~/.claude/commissar/doctrine.history/]")
