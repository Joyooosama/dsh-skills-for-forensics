$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillTarget = Join-Path $env:USERPROFILE '.agents\skills'

New-Item -ItemType Directory -Force -Path $skillTarget | Out-Null

$skillSource = Join-Path $repoRoot 'skills'
if (Test-Path $skillSource) {
    Get-ChildItem -Force $skillSource | Copy-Item -Destination $skillTarget -Recurse -Force
}

$vendorSource = Join-Path $repoRoot 'vendor-drop'
if (Test-Path $vendorSource) {
    Write-Warning 'vendor-drop is present locally. Verify licenses and executable paths before use.'
}

Write-Host "Installed skills into $skillTarget"
Write-Host 'Next: install tools from env\tools.txt and configure the read-only evidence path.'
