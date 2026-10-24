"""Keep THE COMMISSAR up: if service.py does not answer on 127.0.0.1:8791, start it detached and wait for it.
Run at SessionStart (settings.json) and by hand: python -I <ClaudeHome>/commissar/up.py
Prints nothing when she is already up (SessionStart output lands in the context)."""
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def health():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8791/health", timeout=2) as r:
            return json.loads(r.read())
    except (OSError, ValueError):
        return None


def main():
    if health():
        return 0
    exe = sys.executable
    w = os.path.join(os.path.dirname(exe), "pythonw.exe")
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    out = open(os.path.join(HERE, "service.out.log"), "a", encoding="utf-8")
    subprocess.Popen([w if os.path.exists(w) else exe, "-I", os.path.join(HERE, "service.py")], cwd=HERE,
                     stdout=out, stderr=out, stdin=subprocess.DEVNULL, creationflags=flags, close_fds=True)
    for _ in range(40):
        time.sleep(0.5)
        h = health()
        if h:
            print(f"commissar: started (mode {h.get('mode')})")
            return 0
    print("commissar: DID NOT START - see ~/.claude/commissar/service.out.log")
    return 0


if __name__ == "__main__":
    sys.exit(main())
