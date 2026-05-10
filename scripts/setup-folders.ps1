<#
    Sets up the folder structure under the configured base_dir.
    Reads juststatics_config.json from custom_nodes/juststatics_nodes/ if present,
    else uses default ($HOME\juststatics-comfy).
#>
param(
    [string]$BaseDir
)

if (-not $BaseDir) {
    $configPath = Join-Path $PSScriptRoot "..\custom_nodes\juststatics_nodes\juststatics_config.json"
    if (Test-Path $configPath) {
        try {
            $config = Get-Content $configPath -Raw | ConvertFrom-Json
            $BaseDir = $config.base_dir
        } catch {
            Write-Host "Warning: failed to parse $configPath. Using default."
        }
    }
    if (-not $BaseDir) {
        $BaseDir = Join-Path $env:USERPROFILE "juststatics-comfy"
    }
}

Write-Host "Setting up folder structure under: $BaseDir"

$folders = @(
    "needs_edit",
    "processed",
    "approved",
    "in_progress\chain_1",
    "in_progress\chain_2",
    "in_progress\chain_3",
    "in_progress\chain_4",
    "in_progress\chain_5"
)

foreach ($f in $folders) {
    $full = Join-Path $BaseDir $f
    New-Item -ItemType Directory -Force -Path $full | Out-Null
    Write-Host "  $full"
}

Write-Host "`nDone. Drop statics + sidecar JSON files into $BaseDir\needs_edit\"