# Template: copy to <project>\.claude\posttest.ps1 to activate the after-every-edit test gate in that project.
# Must exit 0 on pass, non-zero on failure. Keep it FAST (seconds, not minutes) - it runs after every edit.
# Examples:
#   npm test                 (node projects)
#   python -m pytest -q -x   (python projects)
#   powershell -File .\smoke.ps1
Set-Location $PSScriptRoot\..
npm test
exit $LASTEXITCODE
