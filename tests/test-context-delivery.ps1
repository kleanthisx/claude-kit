# Regression test for Claude Code's per-hook 10,000-character context limit.
# All files created by this test stay in one uniquely named temp directory.
$ErrorActionPreference = 'Stop'
$kit = Split-Path $PSScriptRoot -Parent
$tempBase = [System.IO.Path]::GetFullPath($env:TEMP)
$td = Join-Path $tempBase ('claude-kit-context-' + [guid]::NewGuid().ToString('N'))
$utf8 = New-Object System.Text.UTF8Encoding($false)
$passes = 0
function Check([bool]$condition, [string]$name) {
    if (-not $condition) { throw "FAIL: $name" }
    $script:passes++
    Write-Host "PASS: $name"
}
function Put([string]$path, [string]$body) {
    [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($path)) | Out-Null
    [System.IO.File]::WriteAllText($path, $body, $utf8)
}
function Collect([string]$scriptPath, [string]$inputJson, [int]$configured, [string]$kind) {
    $pieces = New-Object 'System.Collections.Generic.List[string]'
    $hashes = New-Object 'System.Collections.Generic.HashSet[string]'
    $declared = 0
    for ($part = 0; $part -lt $configured; $part++) {
        $raw = $inputJson | powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath -Part $part
        if ($LASTEXITCODE -ne 0) { throw "$kind part $part exited $LASTEXITCODE" }
        if (-not $raw) { continue }
        $output = $raw | ConvertFrom-Json
        $value = [string]$output.hookSpecificOutput.additionalContext
        if ($value -match 'DELIVERY FAILED') { throw $value }
        if ($value.Length -ge 10000) { throw "$kind part $part has $($value.Length) chars" }
        $lineEnd = $value.IndexOf("`n")
        if ($lineEnd -lt 0) { throw "$kind part $part has no part label" }
        $label = $value.Substring(0, $lineEnd)
        if ($label -notmatch '^\[CLAUDE-KIT (MEMORY|WIKI) PART (\d+)/(\d+) SHA256 ([A-F0-9]{64})\]$') {
            throw "$kind part $part has invalid label: $label"
        }
        if ($Matches[1] -ne $kind -or [int]$Matches[2] -ne ($part + 1)) { throw "$kind part $part has wrong label" }
        $declared = [int]$Matches[3]
        [void]$hashes.Add($Matches[4])
        $pieces.Add($value.Substring($lineEnd + 1))
    }
    Check ($pieces.Count -eq $declared -and $declared -gt 1) "${kind}: all $declared numbered parts present"
    Check ($hashes.Count -eq 1) "${kind}: one consistent source snapshot"
    return ($pieces -join '')
}

try {
    $ch = Join-Path $td '.claude'
    $hooks = Join-Path $ch 'hooks'
    [System.IO.Directory]::CreateDirectory($hooks) | Out-Null
    foreach ($name in @('context-part.ps1','session-rules.ps1','load-wiki.ps1')) {
        Copy-Item (Join-Path $kit "hooks\$name") (Join-Path $hooks $name)
    }
    Copy-Item (Join-Path $kit 'doctrine\RULES.md') (Join-Path $ch 'RULES.md')
    $project = Join-Path $td 'project'
    [System.IO.Directory]::CreateDirectory($project) | Out-Null
    $encoded = $project -replace '[^A-Za-z0-9]', '-'
    $memory = Join-Path $ch "projects\$encoded\memory"
    [System.IO.Directory]::CreateDirectory($memory) | Out-Null
    $unicode = [string][char]0x00E9 + [char]0x2014 + [char]::ConvertFromUtf32(0x1F9EA)
    for ($i = 0; $i -lt 60; $i++) {
        $name = 'rule-{0:d2}.md' -f $i
        Put (Join-Path $memory $name) ("RULE-$i $unicode`n" + ('x' * 2350) + "`nEND-RULE-$i")
    }
    Put (Join-Path $memory 'excluded.md') 'EXCLUDED-MARKER'
    Put (Join-Path $memory 'inject-exclude.txt') 'excluded'
    $inputJson = @{ hook_event_name='SessionStart'; source='startup'; cwd=$project } | ConvertTo-Json -Compress
    $memoryText = Collect (Join-Path $hooks 'session-rules.ps1') $inputJson 32 'MEMORY'
    for ($i = 0; $i -lt 60; $i++) {
        Check ($memoryText.Contains("END-RULE-$i")) "memory rule $i delivered"
    }
    Check ($memoryText.Contains($unicode)) 'memory Unicode survived transport'
    Check (-not $memoryText.Contains('EXCLUDED-MARKER')) 'excluded memory omitted'
    Check ($memoryText.Contains('## RULES.md')) 'RULES.md index delivered'

    # The real tier must fit the wired part count (review 2026-10-24: 86 files overflowed 24 parts and the
    # hook delivered only a failure notice; the fake set above never showed it).
    $realProject = Join-Path $td 'real-project'
    [System.IO.Directory]::CreateDirectory($realProject) | Out-Null
    $realEncoded = $realProject -replace '[^A-Za-z0-9]', '-'
    $realMemory = Join-Path $ch "projects\$realEncoded\memory"
    [System.IO.Directory]::CreateDirectory($realMemory) | Out-Null
    foreach ($tier in @('core','core-generalised')) {
        Get-ChildItem (Join-Path $kit "memory\$tier") -Filter *.md -File | Copy-Item -Destination $realMemory
    }
    Copy-Item (Join-Path $kit 'memory\MEMORY.md') (Join-Path $realMemory 'MEMORY.md')
    $realCount = @(Get-ChildItem $realMemory -Filter *.md -File | Where-Object { $_.Name -ne 'MEMORY.md' }).Count
    $realInput = @{ hook_event_name='SessionStart'; source='startup'; cwd=$realProject } | ConvertTo-Json -Compress
    $realText = Collect (Join-Path $hooks 'session-rules.ps1') $realInput 32 'MEMORY'
    Check ($realText.Contains('name: method-core')) "real tier ($realCount files) delivered, method-core present"
    Check (-not $realText.Contains('DELIVERY FAILED')) 'real tier fits the wired memory parts'
    $realChars = ($realText.Length)
    Check ($realChars -lt (32 * 9000 * 0.9)) "real tier leaves headroom ($realChars of $(32*9000) chars)"

    $wiki = Join-Path $project 'docs\wiki'
    [System.IO.Directory]::CreateDirectory((Join-Path $wiki 'entities')) | Out-Null
    [System.IO.Directory]::CreateDirectory((Join-Path $wiki 'doctrine')) | Out-Null
    foreach ($name in @('OVERVIEW.md','DISCARDED.md','NAMES.md','DECISIONS.md')) {
        Put (Join-Path $wiki $name) ("$name $unicode`n" + ('y' * 24500) + "`nEND-$name")
    }
    Put (Join-Path $wiki 'doctrine\method.md') ("DOCTRINE $unicode`n" + ('z' * 14000) + "`nEND-DOCTRINE")
    $wikiText = Collect (Join-Path $hooks 'load-wiki.ps1') $inputJson 40 'WIKI'
    foreach ($name in @('OVERVIEW.md','DISCARDED.md','NAMES.md')) {
        Check ($wikiText.Contains("END-$name")) "wiki $name delivered"
    }
    # DECISIONS.md is on demand since 2026-10-07 (operator): generated, never injected.
    Check (-not $wikiText.Contains('END-DECISIONS.md')) 'wiki DECISIONS.md stays on demand'
    foreach ($name in @()) {
    }
    Check ($wikiText.Contains('END-DOCTRINE')) 'wiki doctrine delivered'
    Check ($wikiText.Contains($unicode)) 'wiki Unicode survived transport'

    $parentJson = @{ hook_event_name='SessionStart'; source='startup'; cwd=$td } | ConvertTo-Json -Compress
    $parentRaw = $parentJson | powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $hooks 'load-wiki.ps1') -Part 0
    $parentNotice = ($parentRaw | ConvertFrom-Json).hookSpecificOutput.additionalContext
    Check ($parentNotice -match 'NO WIKI v2 LOADED' -and $parentNotice -match 'project') 'starting above a wiki warns without guessing'

    $broken = Join-Path $td 'broken-project\docs\wiki\entities'
    [System.IO.Directory]::CreateDirectory($broken) | Out-Null
    $brokenJson = @{ hook_event_name='SessionStart'; source='startup'; cwd=(Split-Path (Split-Path (Split-Path $broken -Parent) -Parent) -Parent) } | ConvertTo-Json -Compress
    $brokenRaw = $brokenJson | powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $hooks 'load-wiki.ps1') -Part 0
    $brokenNotice = ($brokenRaw | ConvertFrom-Json).hookSpecificOutput.additionalContext
    Check ($brokenNotice -match 'DELIVERY FAILED' -and $brokenNotice -match 'NOT loaded') 'missing generated surfaces fail visibly'

    if (Get-Command python -ErrorAction SilentlyContinue) {
        Put (Join-Path $wiki 'generate.py') "import sys`nif '--lint' in sys.argv:`n    print('ERROR intentionally broken')`n    sys.exit(1)`n"
        foreach ($name in @('OVERVIEW.md','DISCARDED.md','NAMES.md','DECISIONS.md')) {
            (Get-Item (Join-Path $wiki $name)).LastWriteTimeUtc = [DateTime]::UtcNow.AddMinutes(1)
        }
        $lintRaw = $inputJson | powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $hooks 'load-wiki.ps1') -Part 0
        $lintNotice = ($lintRaw | ConvertFrom-Json).hookSpecificOutput.additionalContext
        Check ($lintNotice -match 'DELIVERY FAILED' -and $lintNotice -match 'lint found 1 error') 'wiki lint errors fail delivery'
    }

    # An oversized source must fail visibly; no truncated rule text is presented as complete.
    Put (Join-Path $memory 'overflow.md') ('q' * 190000)
    $raw = $inputJson | powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $hooks 'session-rules.ps1') -Part 0
    $failure = ($raw | ConvertFrom-Json).hookSpecificOutput.additionalContext
    Check ($failure -match 'DELIVERY FAILED' -and $failure -match 'NOT loaded') 'overflow is visible, not silent truncation'

    $settings = Get-Content (Join-Path $kit 'settings\hooks.json') -Raw | ConvertFrom-Json
    $commands = @($settings.hooks.SessionStart[0].hooks | ForEach-Object { $_.command })
    Check ((@($commands | Where-Object { $_ -match 'session-rules.ps1 -Part \d+$' })).Count -eq 32) 'settings wires all memory parts'
    Check ((@($commands | Where-Object { $_ -match 'load-wiki.ps1 -Part \d+$' })).Count -eq 40) 'settings wires all wiki parts'
    Check (-not $settings.hooks.PSObject.Properties['PostCompact']) 'no ineffective PostCompact reinjection'
    Write-Output "ALL GREEN: $passes assertions"
} finally {
    $resolved = [System.IO.Path]::GetFullPath($td)
    if ($resolved.StartsWith($tempBase.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase) -and
        [System.IO.Path]::GetFileName($resolved).StartsWith('claude-kit-context-')) {
        Remove-Item -LiteralPath $resolved -Recurse -Force -ErrorAction SilentlyContinue
    }
}
