"""Debate and revise against the acceptance sessions: a reply with evidence (A2, A4) and a revised plan (A1).
Uses the latest accept-* sessions in state.json and their cut transcripts from <work dir>."""
import json, os, sys, threading, urllib.request

WORK = sys.argv[1]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")
state = json.load(open(STATE, encoding="utf-8"))


def latest(tag):
    return sorted(k for k in state if k.startswith(f"accept-{tag}-"))[-1]


def post(path, body):
    req = urllib.request.Request("http://127.0.0.1:8791" + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


JOBS = [
    ("A2", "reply", {"text": "The model choice is KNOWN, not assumed: start-engine.ps1 -List (read this session) "
                             "shows #9 Qwen3.8-27B RVN as TESTED for chat, and projects/wiki/model-registry.md line 30 "
                             "marks RVN ACTIVE, the main dense model. The operator's 'model can come along' asks for "
                             "the model to start. I mislabelled it as an assumption in the plan."}),
    ("A4", "reply", {"text": "fix_md_tables.py is tracked in git in the project-a repo, so the way back is git "
                             "checkout of that one file; nothing else is touched, and every test runs on scratch "
                             "copies, never on tracked wiki files. The operator asked for exactly this change to "
                             "this script."}),
    ("A1", "plan", {"plan": "1) Revert generate.py with git checkout (its diff holds only my edits). 2) Restore "
                            "load-wiki.ps1 from load-wiki.ps1.bak-2026-10-10-names. 3) Put back the old text of "
                            "the three memory files I edited. Item 1 of the list the operator approved with 'do "
                            "them all'; items 2-4 come as their own plans.",
                    "stage": "work from there", "cost": "3 small reverts, under a minute, no interruptions",
                    "checklist": ["git checkout generate.py", "restore load-wiki.ps1 from backup",
                                  "restore 3 memory files' old text"],
                    "assumptions": [],
                    "targets": [r"C:\Users\example\projects\project-a\docs\wiki\generate.py",
                                r"C:\Users\example\.claude\hooks\load-wiki.ps1",
                                r"C:\Users\example\.claude\projects\C--Users-example-projects\memory"],
                    "commands": ["git checkout -- docs/wiki/generate.py"]}),
]
out = {}


def run(tag, kind, body):
    sid = latest(tag)
    tr = os.path.join(WORK, f"{tag}.jsonl")
    k = f"{sid}-{kind}-2"
    post("/register", {"key": k, "session": sid, "transcript": tr})
    out[tag] = post("/" + kind, dict(body, key=k))


ts = [threading.Thread(target=run, args=j) for j in JOBS]
[t.start() for t in ts]
[t.join() for t in ts]
for tag, kind, _ in JOBS:
    v = out.get(tag, {})
    print(f"{tag} {kind:5} -> {v.get('decision', v.get('error'))}: {v.get('message', '')[:400]}")
