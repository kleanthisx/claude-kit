"""The commissar's regression suite for classify.py. Exit 0 when every known case is right, 1 otherwise.

    python -I test_classify.py                 # the known cases
    python -I test_classify.py <calls.jsonl>   # also: the share of a backtest corpus read as changes

Every fixed misread is added below as a known case, so a later repair cannot bring it back.
"""
import collections
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classify import classify  # noqa: E402

KNOWN = [  # (tool, line, expected kind)
    ("Bash", 'python -I -c "import json,sys; s=json.load(open(sys.argv[1],encoding=\'utf-8\')); print(len(s))" x.json', "read-only"),
    ("PowerShell", 'cd C:\\Users\\example\\projects\\claude-kit; Get-ChildItem settings -Recurse -File | ForEach-Object { "{0,7}  {1}" -f $_.Length, $_.FullName }; "--- where"; Select-String -Path settings\\* -Pattern \'x\' | Select-Object -First 8', "read-only"),
    ("PowerShell", "cd C:\\x; git diff --stat settings/hooks.json; git diff settings/hooks.json | Select-String '^[+-]' | Where-Object { $_.Line -notmatch '^(\\+\\+\\+|---)' } | ForEach-Object { $_.Line }", "read-only"),
    ("PowerShell", "python -I C:\\Users\\example\\.claude\\hooks\\pre-action-review.py --session bd266ad4 --asks", "changes"),
    ("PowerShell", 'Copy-Item "$env:USERPROFILE\\.claude\\hooks\\a.py" hooks\\a.py', "changes"),
    ("PowerShell", "git commit -q -F C:\\msg.txt", "changes"),
    ("PowerShell", "$s = Get-Content x.json -Raw | ConvertFrom-Json; $s.hooks", "read-only"),
    ("PowerShell", 'if (Test-Path x) { "yes" } else { "no" }', "read-only"),
    ("PowerShell", "Stop-Process -Id 42 -Force", "changes"),
    ("PowerShell", "Remove-Item x -Recurse", "changes"),
    ("Bash", "ls -la && git status -s | head -5", "read-only"),
    ("Bash", "git log --oneline -3 2>/dev/null", "read-only"),
    ("Bash", "echo hi > notes.txt", "changes"),
    ("Bash", "rm -rf build/", "changes"),
    ("Bash", "git push origin main", "changes"),
    ("Bash", "git branch -vv", "read-only"),
    ("Bash", "git branch -D old", "changes"),
    ("Bash", "sed -n '6,22p' x.md", "read-only"),
    ("Bash", "sed -i 's/a/b/' x.md", "changes"),
    ("Bash", "curl -sS https://x.org/a -o out.html", "changes"),
    ("Bash", "curl -sS https://x.org/a | head", "read-only"),
    ("PowerShell", "nvidia-smi --query-gpu=memory.used --format=csv,noheader", "read-only"),
    ("PowerShell", "(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8791/health -TimeoutSec 5).Content; Get-Content x.log | Select-Object -Last 3", "read-only"),
    ("PowerShell", "(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8791/health -TimeoutSec 5).Content; Get-Content C:\\Users\\example\\.claude\\commissar\\commissar.log.jsonl -Encoding UTF8 -Tail 2 | ForEach-Object { $_.Substring(0, [Math]::Min(200, $_.Length)) }", "read-only"),
]

PATH_KNOWN = [  # quoted prose is not a file operand
    ("PowerShell", 'Write-Output "design/decision entries"', []),
    ("PowerShell", '$j.plan = "skills/enter/SKILL.md"', []),
]


def main():
    bad = 0
    for tool, line, want in KNOWN:
        got = classify(tool, line)["kind"]
        if got != want:
            bad += 1
            print(f"FAIL  {tool:10} want {want:9} got {got:9} {line[:120]}")
    for tool, line, want in PATH_KNOWN:
        got = classify(tool, line)["paths"]
        if got != want:
            bad += 1
            print(f"FAIL  {tool:10} want paths {want!r} got {got!r} {line[:120]}")

    # Gate regressions: a listed command cannot bless an unlisted prefix, and executing a scratch script is
    # opaque rather than inherently scratch-only.
    from service import Commissar, TEMP_CLAUDE  # noqa: E402
    gate = Commissar()
    gate.state = {}
    listed = gate.sess("listed-regression")
    listed.update(status="approved", msg_hash="", commands=["git status"], targets=[])
    line = r"Remove-Item C:\outside.txt; git status"
    decision, _ = gate.check("listed-regression", "", "PowerShell", {"command": line}, "C:\\")
    if decision != "deny":
        bad += 1
        print(f"FAIL  PowerShell want deny got {decision} {line}")
    scratch = os.path.join(TEMP_CLAUDE, "session", "scratchpad", "unreviewed.py")
    line = f'python -I "{scratch}"'
    decision, _ = gate.check("scratch-regression", "", "PowerShell", {"command": line}, "C:\\")
    if decision != "deny":
        bad += 1
        print(f"FAIL  PowerShell want deny got {decision} {line}")

    total = len(KNOWN) + len(PATH_KNOWN) + 2
    print(f"known cases: {total - bad}/{total} right")
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        n = collections.Counter()
        for l in open(sys.argv[1], encoding="utf-8"):
            c = json.loads(l)
            if c["tool"] in ("Bash", "PowerShell"):
                n[classify(c["tool"], c["input"].get("command", ""))["kind"]] += 1
        total = sum(n.values())
        print(f"corpus: {total} commands, {100 * n['changes'] / max(total, 1):.0f}% read as changes")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
