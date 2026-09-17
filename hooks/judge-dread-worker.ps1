# JUDGE DREAD -- the worker. Runs DETACHED, off the session's critical path.
#
# Why this file exists: a Stop hook is synchronous. Claude Code waits for it to
# exit before the turn ends, so every second the judge spent thinking was a
# second the session sat frozen -- measured at 2m44s on a real turn once he
# started opening files for himself.
#
# So the hook no longer judges. It gathers evidence, drops it here, and returns
# immediately. This worker does the slow part in its own process and writes a
# single verdict line to $OutFile. The next Stop hook picks that up and rules.
#
# The cost of that is honest and worth stating: enforcement lags by one turn.
# Dread rules on the turn BEFORE the one you are in. He still blocks, the block
# just arrives one beat late.
#
# This script must never write anything except $OutFile, and must always remove
# $LockFile -- a lock left behind makes the dispatcher think a judge is still
# thinking, and it would stop dispatching new ones.
param($PayloadFile, $PromptFile, $OutFile, $LockFile)
$ErrorActionPreference = 'SilentlyContinue'
# Capture the CLI's output as UTF-8. Without this the console's ANSI codepage
# mangles anything non-ASCII on the way in, and a verdict came back reading
# "hardcoded literal string ΓÇö no records are counted" instead of an em-dash.
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
try {
    $payload = [IO.File]::ReadAllText($PayloadFile)
    $prompt = [IO.File]::ReadAllText($PromptFile)

    # No Haiku anywhere in this call -- see the note in judge-dread.ps1.
    $env:CLAUDE_HOOK_JUDGE = '1'
    $env:ANTHROPIC_SMALL_FAST_MODEL = 'claude-sonnet-5'
    $verdict = $payload | claude -p $prompt --model claude-sonnet-5 `
        --allowedTools Read Grep Glob `
        --disallowedTools Write Edit Bash PowerShell Agent Task WebFetch WebSearch `
        --settings (Join-Path $PSScriptRoot 'judge-settings.json') 2>$null

    if ($LASTEXITCODE -ne 0 -or -not $verdict) {
        $line = 'UNAVAILABLE'
    } else {
        # Dread uses tools, so his reply is not guaranteed to BE the verdict --
        # he may narrate a file read first. Scan upward for the last line that
        # opens with a verdict token. @() is load-bearing: without it a one-line
        # reply stays a scalar string and $all[0] indexes a CHARACTER.
        $all = @(($verdict | Out-String) -split "`r?`n" | Where-Object { $_.Trim() })
        $line = ''
        for ($k = $all.Count - 1; $k -ge 0; $k--) {
            if ($all[$k] -match '(?i)^\s*(FAITHFUL|UNBACKED|SUBSTITUTED|OMITTED)') { $line = $all[$k].Trim(); break }
        }
        if (-not $line) { $line = 'MALFORMED' }

        # A verdict of "UNBACKED: none ..." is a PASS wearing a failure token.
        # Seen live: "UNBACKED: none no work was claimed; the reply only says
        # goodnight" -- the judge correctly found nothing wrong and then reached
        # for the wrong word, and the parser blocked a turn that claimed nothing.
        # A false block costs a turn and, worse, teaches the reader to discount
        # him. Real reasons never open with "none"/"nothing"/"n/a".
        # ANCHORED AT THE END, deliberately. A looser "starts with none" rule
        # also swallowed "UNBACKED: none of the three scripts were executed,
        # so the counts are asserted" -- a REAL block, converted into an
        # approval. False block costs one turn; false pass costs the tool. So
        # this fires only when the entire reason is none/nothing/n-a, and the
        # prompt carries the instruction that stops the rest at source.
        if ($line -match '(?i)^\s*(UNBACKED|SUBSTITUTED|OMITTED)\s*:\s*(none|nothing|n/?a)\s*[.!]?\s*$') {
            $line = 'FAITHFUL'
        }
    }
    # Belt and braces with the ASCII-only instruction in the prompt: whatever
    # survives the console codepage, force it to printable ASCII before it goes
    # anywhere near the session. Setting Console::OutputEncoding alone did not
    # fix it -- it only changed which mojibake appeared.
    $line = ($line -replace '[^\x20-\x7E]', ' ') -replace '\s{2,}', ' '
    [IO.File]::WriteAllText($OutFile, $line.Trim())
} catch {
    [IO.File]::WriteAllText($OutFile, 'UNAVAILABLE')
} finally {
    Remove-Item -LiteralPath $LockFile -Force -ErrorAction SilentlyContinue
}
