import json, os, subprocess, sys

HOOK = os.environ.get("KIT_HOOK_DIR") and os.path.join(os.environ["KIT_HOOK_DIR"], "guard-destructive.ps1") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks", "guard-destructive.ps1")
REAL = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Documents", "real-target")   # a non-temp path: temp-bypass must NOT apply

# (label, command, expected)  expected: "ASK" (must be caught) or "PASS" (must not fire)
cases = [
    # --- the holes the reviewers deleted real files through: MUST now ASK ---
    ("py-shutil-rmtree", f'python -c "import shutil; shutil.rmtree(r\'{REAL}\')"', "ASK"),
    ("py-os-remove",     f'python -c "import os; os.remove(r\'{REAL}\\f.txt\')"', "ASK"),
    ("py-os-rmdir",      f'python -c "import os; os.rmdir(r\'{REAL}\')"', "ASK"),
    ("py-pathlib-unlink",f'python -c "import pathlib; pathlib.Path(r\'{REAL}\\f\').unlink()"', "ASK"),
    ("py-pathlib-rmdir", f'python -c "import pathlib; pathlib.Path(r\'{REAL}\').rmdir()"', "ASK"),
    ("py-from-rmtree",   f'python -c "from shutil import rmtree; rmtree(r\'{REAL}\')"', "ASK"),
    ("ps-rm-recurse",    f'powershell -NoProfile -Command "rm -Recurse -Force {REAL}"', "ASK"),
    ("ps-rm-rec-abbr",   f'powershell -NoProfile -Command "rm -rec -Force {REAL}"', "ASK"),
    ("ps-rmdir-recurse", f'powershell -NoProfile -Command "rmdir -Recurse -Force {REAL}"', "ASK"),
    ("ps-remove-item",   f'powershell -NoProfile -Command "Remove-Item -Recurse -Force {REAL}"', "ASK"),
    ("pwsh-remove-item", f'pwsh -c "Remove-Item -Recurse -Force {REAL}"', "ASK"),
    ("ps-rm-r-sep",      f'powershell -Command "rm -r {REAL}"', "ASK"),
    # --- previously-caught dangerous: MUST still ASK ---
    ("naked-rm-rf",      f'rm -rf {REAL}', "ASK"),
    ("naked-rm-fr",      f'rm -fr {REAL}', "ASK"),
    ("naked-rm-r-f",     f'rm -r -f {REAL}', "ASK"),
    ("naked-remove-item",f'Remove-Item -Recurse -Force {REAL}', "ASK"),
    ("ri-alias",         f'ri -r -fo {REAL}', "ASK"),
    ("piped-remove",     f'Get-ChildItem {REAL} | Remove-Item -Recurse -Force', "ASK"),
    ("piped-rm",         f'gci {REAL} | rm -Recurse -Force', "ASK"),
    ("cmd-rmdir-s",      f'cmd /c rmdir /s /q {REAL}', "ASK"),
    ("dotnet-dir-delete",f"[System.IO.Directory]::Delete('{REAL}', $true)", "ASK"),
    ("dotnet-file-delete",f"[System.IO.File]::Delete('{REAL}\\f.txt')", "ASK"),
    ("del-s",            f'del /s /q {REAL}', "ASK"),
    ("git-force",        'git push --force origin main', "ASK"),
    ("git-reset-hard",   'git reset --hard HEAD~1', "ASK"),
    ("git-stash-bare",   'git stash', "ASK"),
    # --- benign: MUST NOT ask (no false positives) ---
    ("echo",             'echo hello world', "PASS"),
    ("ls",               'ls -la', "PASS"),
    ("git-status",       'git status', "PASS"),
    ("git-force-lease",  'git push --force-with-lease origin main', "PASS"),
    ("git-stash-pop",    'git stash pop', "PASS"),
    ("py-print",         'python -c "print(1)"', "PASS"),
    ("py-exists",        f'python -c "import os; print(os.path.exists(r\'{REAL}\'))"', "PASS"),
    # NOTE 2026-09-16: this still expects PASS, but for a DIFFERENT reason than when it was
    # written. Gap B is now closed -- the guard reads the contents of a script the command
    # launches. `train.py` does not exist on disk during this suite, and a script that cannot
    # be read cannot be scanned, so it is allowed. Do NOT read this case as "script bodies are
    # never inspected"; the live gap-B cases with real fixtures are in test-hooks.ps1.
    ("py-script",        'python train.py --epochs 3', "PASS"),
    ("move-item",        'Move-Item a.txt b.txt', "PASS"),
    ("new-item",         'New-Item -ItemType Directory foo', "PASS"),
    ("remove-variable",  'Remove-Variable -Force x', "PASS"),
    ("npm-test",         'npm test', "PASS"),
    # FLIPPED 2026-09-16 from PASS to ASK. This case asserted that deleting a NAMED file is
    # allowed silently -- encoded design, not an oversight. It was wrong twice in practice: four
    # experiment-run artifacts and an untracked build_catalog.py, all unrecoverable. Named-file
    # deletion is exactly as irreversible as recursive deletion, which this guard already asks on.
    # Noise measured before flipping: 2 prompts across the last 12 session transcripts.
    ("plain-rm-file",    'rm notes.txt', "ASK"),
    ("path-with-rd",     'cat C:\\Users\\example\\rd\\config.txt', "PASS"),
    ("path-with-farm",   'cd C:\\Users\\example\\projects\\farm-tools', "PASS"),
    ("copy",             'copy a.txt b.txt', "PASS"),
]

def fires(cmd):
    payload = json.dumps({"tool_input": {"command": cmd}})
    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", HOOK],
        input=payload, capture_output=True, text=True)
    return "permissionDecision" in r.stdout and "ask" in r.stdout

fails = 0
for label, cmd, exp in cases:
    got = "ASK" if fires(cmd) else "PASS"
    ok = (got == exp)
    if not ok:
        fails += 1
    print(f"{'PASS' if ok else 'FAIL'}  [{label}] expected={exp} got={got}")

print(f"\n{'ALL GREEN' if fails == 0 else str(fails) + ' FAILURES'}  ({len(cases)} cases)")
sys.exit(1 if fails else 0)
