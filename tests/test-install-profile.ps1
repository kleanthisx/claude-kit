# Installer regression: exercise both profiles against a disposable kit copy and Claude home.
# Never touches the real ~/.claude, home CLAUDE.md, or the repo's runtime hook log.
$ErrorActionPreference = 'Stop'
$kit = Split-Path $PSScriptRoot -Parent
$tempBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\')
$root = Join-Path $tempBase ('claude-kit-install-test-' + [guid]::NewGuid().ToString('N'))
$source = Join-Path $root 'kit'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$passes = 0
$complete = $false

function Check([bool]$condition, [string]$label) {
    if (-not $condition) { throw "FAIL: $label" }
    $script:passes++
    Write-Host "PASS: $label"
}
function Put([string]$path, [string]$body) {
    [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($path)) | Out-Null
    [System.IO.File]::WriteAllText($path, $body, $utf8)
}
function Run-Installer([string]$profile, [string]$claudeHome, [string]$memory, [string]$doctrine,
                       [switch]$preview, [switch]$uninstall, [string[]]$extra = @()) {
    $args = @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $source 'install.ps1'),
              '-Profile',$profile,'-ClaudeHome',$claudeHome,'-MemoryDir',$memory,
              '-UserDoctrinePath',$doctrine,
              '-ClaudeJsonPath',(Join-Path $claudeHome 'isolated.claude.json'))
    if ($preview) { $args += '-WhatIf' }
    if ($uninstall) { $args += '-Uninstall' }
    $args += $extra
    $output = & powershell @args 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { throw "installer exited $LASTEXITCODE`n$output" }
    return $output
}
function Check-Coverage([string]$dir, [string]$label) {
    $files = @(Get-ChildItem $dir -Filter *.md -File | Where-Object {
        $_.Name -notin @('MEMORY.md','MEMORY.personal.md')
    } | ForEach-Object { $_.Name })
    $index = [System.IO.File]::ReadAllText((Join-Path $dir 'MEMORY.md'), [System.Text.Encoding]::UTF8)
    $links = @([regex]::Matches($index, '\]\(([^)]+\.md)\)') |
        ForEach-Object { [System.IO.Path]::GetFileName($_.Groups[1].Value) })
    Check ($files.Count -gt 0 -and $files.Count -eq $links.Count) "${label}: one index link per installed memory file"
    Check (@($files | Where-Object { $links -notcontains $_ }).Count -eq 0) "${label}: no unindexed files"
    Check (@($links | Where-Object { $files -notcontains $_ }).Count -eq 0) "${label}: no dead links"
}

try {
    [System.IO.Directory]::CreateDirectory($source) | Out-Null
    Copy-Item (Join-Path $kit 'install.ps1') (Join-Path $source 'install.ps1')
    foreach ($folder in @('hooks','skills','agents','tools','doctrine','memory','settings','commissar','conclave')) {
        Copy-Item -LiteralPath (Join-Path $kit $folder) -Destination (Join-Path $source $folder) -Recurse
    }
    [System.IO.Directory]::CreateDirectory((Join-Path $source 'tests')) | Out-Null
    Copy-Item -LiteralPath (Join-Path $kit 'tests\fixtures') -Destination (Join-Path $source 'tests\fixtures') -Recurse

    # A gitignored source log and an existing live log reproduce the reported collision.
    Put (Join-Path $source 'hooks\launch-gate.log') 'STALE SOURCE LOG'
    Put (Join-Path $source 'hooks\unrelated.tmp') 'NOT AN INSTALLABLE HOOK'
    $homeRule = 'install-fixture-home-only.md'
    Put (Join-Path $source "memory\personal\$homeRule") '# Home-only fixture rule'
    $personalIndex = Join-Path $source 'memory\personal\MEMORY.personal.md'
    $oldPersonalIndex = if (Test-Path $personalIndex) {
        [System.IO.File]::ReadAllText($personalIndex, [System.Text.Encoding]::UTF8)
    } else { "# Home index`n" }
    Put $personalIndex ($oldPersonalIndex + "`n- [Home-only fixture]($homeRule) - installer test`n")

    $previewHome = Join-Path $root 'preview-home'
    $previewMemory = Join-Path $previewHome 'projects\preview\memory'
    $previewDoctrine = Join-Path $root 'preview-CLAUDE.md'
    $null = Run-Installer 'home' $previewHome $previewMemory $previewDoctrine -preview
    Check (-not (Test-Path $previewHome) -and -not (Test-Path $previewDoctrine)) 'WhatIf makes no writes'

    $workHome = Join-Path $root 'work-home'
    $workMemory = Join-Path $workHome 'projects\work\memory'
    $workDoctrine = Join-Path $root 'work-CLAUDE.md'
    $workOutput = Run-Installer 'work' $workHome $workMemory $workDoctrine
    Check-Coverage $workMemory 'work profile'
    Check (-not (Test-Path (Join-Path $workMemory $homeRule))) 'work profile excludes home-only memory'
    Check (-not (Test-Path (Join-Path $workHome 'hooks\launch-gate.log'))) 'source runtime log is not installed'
    Check (-not (Test-Path (Join-Path $workHome 'hooks\unrelated.tmp'))) 'arbitrary hook files are not installed'
    Check ($workOutput -match '0 unindexed, 0 dead links') 'work install reports complete index'
    $workSettingsHash = (Get-FileHash (Join-Path $workHome 'settings.json')).Hash
    $workBackups = @(Get-ChildItem $workHome -Filter 'settings.json.claude-kit-*.bak').Count
    $null = Run-Installer 'work' $workHome $workMemory $workDoctrine
    Check ((Get-FileHash (Join-Path $workHome 'settings.json')).Hash -eq $workSettingsHash) 'reinstall leaves settings unchanged'
    Check (@(Get-ChildItem $workHome -Filter 'settings.json.claude-kit-*.bak').Count -eq $workBackups) 'reinstall creates no backup'
    Check (-not (Test-Path (Join-Path $workHome 'skills\commissar'))) 'commissar skill is not installed without -WithCommissar'
    Check (-not (Test-Path (Join-Path $workHome 'hooks\commissar-gate.py'))) 'commissar gate is not installed without -WithCommissar'

    # --- optional layer: -WithCommissar
    $cHome = Join-Path $root 'commissar-home'
    $cMemory = Join-Path $cHome 'projects\c\memory'
    $cDoctrine = Join-Path $root 'commissar-CLAUDE.md'
    $cJson = Join-Path $cHome 'isolated.claude.json'
    Put $cJson '{"mcpServers":{"other":{"type":"stdio","command":"x","args":[]}},"keep":1}'
    $null = Run-Installer 'work' $cHome $cMemory $cDoctrine -extra @('-WithCommissar')
    $cHomeFwd = $cHome -replace '\\','/'
    Check ((Test-Path (Join-Path $cHome 'commissar\service.py')) -and (Test-Path (Join-Path $cHome 'commissar\up.py'))) 'commissar code installed'
    Check ((Test-Path (Join-Path $cHome 'commissar\config.json'))) 'commissar config installed'
    Check (-not (Test-Path (Join-Path $cHome 'commissar\state.json'))) 'commissar state is not shipped'
    Check ((Test-Path (Join-Path $cHome 'hooks\commissar-gate.py'))) 'commissar gate installed'
    $cSkill = [System.IO.File]::ReadAllText((Join-Path $cHome 'skills\commissar\SKILL.md'), [System.Text.Encoding]::UTF8)
    Check ($cSkill.Contains("$cHomeFwd/commissar/talk.py") -and -not $cSkill.Contains('{{CLAUDE_HOME}}')) 'commissar skill names the installed path'
    $cSettings = [System.IO.File]::ReadAllText((Join-Path $cHome 'settings.json'), [System.Text.Encoding]::UTF8) | ConvertFrom-Json
    $cCmds = @($cSettings.hooks.PSObject.Properties.Value | ForEach-Object { $_ } | ForEach-Object { $_.hooks } | ForEach-Object { $_.command })
    Check (@($cCmds | Where-Object { $_ -match 'commissar-gate\.py$' }).Count -eq 1) 'settings wire the commissar gate once'
    Check (@($cCmds | Where-Object { $_ -match 'commissar/up\.py$' }).Count -eq 1) 'settings start the commissar once at SessionStart'
    $cj = [System.IO.File]::ReadAllText($cJson, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
    Check (($cj.mcpServers.commissar.args -join ' ') -eq "-I $cHomeFwd/commissar/mcp_server.py") 'mcpServers.commissar registered with the installed path'
    Check ($cj.mcpServers.other.command -eq 'x' -and $cj.keep -eq 1) 'other MCP servers and keys survive'
    Put (Join-Path $cHome 'commissar\config.json') '{"mode":"enforce","effort":"high"}'
    $cSettingsHash = (Get-FileHash (Join-Path $cHome 'settings.json')).Hash
    $cJsonHash = (Get-FileHash $cJson).Hash
    $cOut = Run-Installer 'work' $cHome $cMemory $cDoctrine -extra @('-WithCommissar')
    Check ((Get-FileHash (Join-Path $cHome 'settings.json')).Hash -eq $cSettingsHash) 'commissar reinstall leaves settings unchanged'
    Check ((Get-FileHash $cJson).Hash -eq $cJsonHash) 'commissar reinstall leaves .claude.json unchanged'
    Check (([System.IO.File]::ReadAllText((Join-Path $cHome 'commissar\config.json')) -match 'enforce') -and ($cOut -match 'PRESERVED: commissar\\config.json')) 'her config survives a reinstall'
    $null = Run-Installer 'work' $cHome $cMemory $cDoctrine -uninstall
    Check (-not (Test-Path (Join-Path $cHome 'commissar\service.py')) -and -not (Test-Path (Join-Path $cHome 'hooks\commissar-gate.py'))) 'uninstall removes her code and gate'
    Check ((Test-Path (Join-Path $cHome 'commissar\config.json'))) 'uninstall leaves her config'
    $cj2 = [System.IO.File]::ReadAllText($cJson, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
    Check ((-not $cj2.mcpServers.PSObject.Properties['commissar']) -and $cj2.mcpServers.other.command -eq 'x') 'uninstall removes only our MCP entry'

    # --- optional layer: -WithConclave (on the same home: the two layers must coexist)
    $vRoot = Join-Path $root 'council-project'
    $null = Run-Installer 'work' $cHome $cMemory $cDoctrine -extra @('-WithConclave','-Council','council-a','-ConclaveProjectRoot',$vRoot)
    $vRootFwd = $vRoot -replace '\\','/'
    Check ((Test-Path (Join-Path $cHome 'conclave\core.py')) -and (Test-Path (Join-Path $cHome 'conclave\claude_hook.py'))) 'conclave code installed'
    Check (-not (Test-Path (Join-Path $cHome 'conclave\HANDOFF_TO_CLAUDE.md')) -and -not (Test-Path (Join-Path $cHome 'conclave\TODO.md'))) 'conclave project notes are not installed'
    $vSettings = [System.IO.File]::ReadAllText((Join-Path $cHome 'settings.json'), [System.Text.Encoding]::UTF8) | ConvertFrom-Json
    $vCmds = @($vSettings.hooks.PSObject.Properties.Value | ForEach-Object { $_ } | ForEach-Object { $_.hooks } | ForEach-Object { $_.command })
    $vHook = @($vCmds | Where-Object { $_ -match 'conclave/claude_hook\.py' })
    Check ($vHook.Count -eq 2) 'settings wire the conclave hook on UserPromptSubmit and PreToolUse'
    Check (@($vHook | Where-Object { $_ -match "--council council-a --mode observe --project-root $([regex]::Escape($vRootFwd))$" }).Count -eq 2) 'conclave hooks carry the council, observe mode and the project root'
    Check (-not ($vHook -join ' ').Contains('{{')) 'no placeholder left in the conclave hook lines'
    $vj = [System.IO.File]::ReadAllText($cJson, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
    Check (($vj.mcpServers.conclave.args -join ' ') -eq "-I $cHomeFwd/conclave/mcp_server.py --actor claude --council council-a") 'mcpServers.conclave registered with actor, council and installed path'
    Check ($vj.mcpServers.other.command -eq 'x' -and $vj.keep -eq 1) 'other MCP servers survive the conclave registration'
    $vSettingsHash = (Get-FileHash (Join-Path $cHome 'settings.json')).Hash
    $vJsonHash = (Get-FileHash $cJson).Hash
    $null = Run-Installer 'work' $cHome $cMemory $cDoctrine -extra @('-WithConclave','-Council','council-a','-ConclaveProjectRoot',$vRoot)
    Check ((Get-FileHash (Join-Path $cHome 'settings.json')).Hash -eq $vSettingsHash) 'conclave reinstall leaves settings unchanged'
    Check ((Get-FileHash $cJson).Hash -eq $vJsonHash) 'conclave reinstall leaves .claude.json unchanged'
    $null = Run-Installer 'work' $cHome $cMemory $cDoctrine -uninstall
    Check (-not (Test-Path (Join-Path $cHome 'conclave\core.py'))) 'uninstall removes the conclave code'
    $vj2 = [System.IO.File]::ReadAllText($cJson, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
    Check ((-not $vj2.mcpServers.PSObject.Properties['conclave']) -and $vj2.mcpServers.other.command -eq 'x') 'uninstall removes only the conclave MCP entry'

    $targetHome = Join-Path $root 'home-home'
    $memory = Join-Path $targetHome 'projects\home\memory'
    $doctrine = Join-Path $root 'home-CLAUDE.md'
    $liveLog = Join-Path $targetHome 'hooks\launch-gate.log'
    Put $liveLog 'LIVE LOG - KEEP'
    $homeOutput = Run-Installer 'home' $targetHome $memory $doctrine
    Check-Coverage $memory 'home profile'
    Check ((Test-Path (Join-Path $memory $homeRule))) 'home profile installs home-only memory'
    Check (-not (Test-Path (Join-Path $memory 'MEMORY.personal.md'))) 'personal index is not installed as a second index'
    Check ([System.IO.File]::ReadAllText($liveLog) -eq 'LIVE LOG - KEEP') 'live log survives install'
    Check ($homeOutput -match '0 unindexed, 0 dead links') 'home install reports complete index'

    # A local index may be newer than the portable kit. Preserve it byte-for-byte on update.
    $localRule = Join-Path $memory 'local-only.md'
    Put $localRule '# Local memory rule'
    $customIndex = Join-Path $memory 'MEMORY.md'
    Put $customIndex "# LIVE INDEX`n- [Local rule](local-only.md)`n"
    $customHash = (Get-FileHash $customIndex).Hash
    $localExclude = Join-Path $memory 'inject-exclude.txt'
    Put $localExclude "# LOCAL EXCLUSION LIST`nlocal-only`n"
    $excludeHash = (Get-FileHash $localExclude).Hash
    $updateOutput = Run-Installer 'home' $targetHome $memory $doctrine
    Check ((Get-FileHash $customIndex).Hash -eq $customHash) 'existing local MEMORY.md survives update byte-for-byte'
    Check ($updateOutput -match 'PRESERVED: existing MEMORY.md') 'installer reports preservation of local index'
    Check ((Get-FileHash $localExclude).Hash -eq $excludeHash) 'existing local exclusion list survives update byte-for-byte'
    Check ($updateOutput -match 'PRESERVED: local inject-exclude.txt differs') 'installer reports exclusion-list conflict'
    Check ([System.IO.File]::ReadAllText($liveLog) -eq 'LIVE LOG - KEEP') 'live log survives update'

    $null = Run-Installer 'home' $targetHome $memory $doctrine -uninstall
    Check ([System.IO.File]::ReadAllText($liveLog) -eq 'LIVE LOG - KEEP') 'live log survives uninstall'
    Check ((Get-FileHash $customIndex).Hash -eq $customHash) 'local memory survives uninstall'
    Write-Host "ALL GREEN: $passes installer assertions"
    $complete = $true
} finally {
    if ($complete) {
        $resolvedRoot = [System.IO.Path]::GetFullPath($root)
        if ((Split-Path $resolvedRoot -Parent) -ne $tempBase) {
            throw "Refusing cleanup outside test temp parent: $resolvedRoot"
        }
        Remove-Item -LiteralPath $resolvedRoot -Recurse -Force
    } else {
        Write-Warning "Installer test artifacts retained for inspection: $root"
    }
}
