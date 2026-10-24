"""Read pre-action-log.jsonl (written by pre-action-log.py, shadow mode) and show what a pre-action check
would have done.

    python pre-action-review.py                  # every session in the log
    python pre-action-review.py --session 1a2b    # one session (id prefix)
    python pre-action-review.py --asks            # also list every "would ask" call
"""
import collections
import json
import os
import sys

LOG = os.environ.get("PRE_ACTION_LOG_FILE") or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                             "pre-action-log.jsonl")


def main():
    args = sys.argv[1:]
    sess = args[args.index("--session") + 1] if "--session" in args else ""
    recs = []
    with open(LOG, encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("session", "").startswith(sess):
                recs.append(r)
    if not recs:
        print("no records" + (f" for session {sess}" if sess else ""))
        return 0
    errors = [r for r in recs if "error" in r]
    ok = [r for r in recs if "verdict" in r]
    print(f"{len(recs)} calls, {len(errors)} errors, sessions: {', '.join(sorted({r.get('session', '?') for r in recs}))}")
    by = collections.Counter((r["tool"], r["verdict"]) for r in ok)
    print("\n| tool | verdict | calls |\n|---|---|---|")
    for (tool, verdict), n in sorted(by.items()):
        print(f"| {tool} | {verdict} | {n} |")
    asks = [r for r in ok if r["verdict"] == "would ask"]
    print(f"\nwould ask: {len(asks)} of {len(ok)} calls ({100 * len(asks) / len(ok):.0f}%)")
    ms = sorted(r.get("ms", 0) for r in recs)
    print(f"check time: median {ms[len(ms) // 2]} ms, p90 {ms[int(len(ms) * 0.9)]} ms, max {ms[-1]} ms")
    for r in errors[:10]:
        print(f"ERROR {r['t']} {r['error']}")
    if "--asks" in args:
        print()
        for r in asks:
            what = r.get("target") or r.get("command", "")
            print(f"{r['t']}  {r['tool']}: {what[:140]}")
            print(f"    why: {'; '.join(r.get('reasons', []))}")
            print(f"    operator said: {r.get('user_msg', '')[:160]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
