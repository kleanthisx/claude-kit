# Shared output routine for SessionStart context hooks. Claude Code caps each
# additionalContext string at 10,000 characters, independently per hook.
function Write-KitContextPart {
    param(
        [Parameter(Mandatory=$true)][string]$Context,
        [Parameter(Mandatory=$true)][string]$Kind,
        [Parameter(Mandatory=$true)][string]$EventName,
        [Parameter(Mandatory=$true)][int]$Part,
        [Parameter(Mandatory=$true)][int]$PartCount
    )

    $bodyLimit = 9000
    $bounds = New-Object 'System.Collections.Generic.List[int]'
    $bounds.Add(0)
    while ($bounds[$bounds.Count - 1] -lt $Context.Length) {
        $start = $bounds[$bounds.Count - 1]
        $end = [Math]::Min($start + $bodyLimit, $Context.Length)
        if ($end -lt $Context.Length) {
            # Prefer a line boundary near the end, but never lose a character.
            $near = $Context.LastIndexOf("`n", $end - 1, [Math]::Min(500, $end - $start))
            if ($near -ge ($end - 500)) { $end = $near + 1 }
            # A supplementary Unicode character must not be split across hooks.
            if ([char]::IsHighSurrogate($Context[$end - 1])) { $end-- }
        }
        $bounds.Add($end)
    }
    $needed = $bounds.Count - 1

    if ($needed -gt $PartCount) {
        if ($Part -ne 0) { return }
        $body = "CLAUDE-KIT CONTEXT DELIVERY FAILED ($Kind): $needed parts required; only $PartCount configured. " +
            'The full instructions were NOT loaded. Stop project work, report this to the operator, ' +
            'and increase the SessionStart hook part count in claude-kit before continuing.'
    } elseif ($Part -ge $needed) {
        return
    } else {
        $sha = [System.Security.Cryptography.SHA256]::Create()
        try {
            $hash = [BitConverter]::ToString($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Context))).Replace('-', '')
        } finally { $sha.Dispose() }
        $label = "[CLAUDE-KIT $Kind PART $($Part + 1)/$needed SHA256 $hash]`n"
        $body = $label + $Context.Substring($bounds[$Part], $bounds[$Part + 1] - $bounds[$Part])
    }

    if ($body.Length -ge 10000) { throw "Context part exceeds Claude Code's 10,000-character limit" }
    $payload = [pscustomobject]@{
        hookSpecificOutput = [pscustomobject]@{
            hookEventName = $EventName
            additionalContext = $body
        }
    }
    $json = $payload | ConvertTo-Json -Depth 6 -Compress
    $out = New-Object System.Text.StringBuilder
    foreach ($ch in $json.ToCharArray()) {
        if ([int]$ch -gt 126) { [void]$out.AppendFormat('\u{0:x4}', [int]$ch) }
        else { [void]$out.Append($ch) }
    }
    [Console]::Out.Write($out.ToString())
}
