<#
    Generates 5 dummy sidecar JSON files in needs_edit/ for testing.
    Place 5 image files (kunde_a_static_001.jpg through kunde_e_static_001.jpg) manually first.
#>
param(
    [string]$NeedsEditDir
)

if (-not $NeedsEditDir) {
    $configPath = Join-Path $PSScriptRoot "..\custom_nodes\juststatics_nodes\juststatics_config.json"
    if (Test-Path $configPath) {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
        $NeedsEditDir = Join-Path $config.base_dir "needs_edit"
    } else {
        $NeedsEditDir = Join-Path $env:USERPROFILE "juststatics-comfy\needs_edit"
    }
}

if (-not (Test-Path $NeedsEditDir)) {
    Write-Host "Folder not found: $NeedsEditDir. Run setup-folders.ps1 first."
    exit 1
}

$cases = @(
    @{ id = "kunde_a"; navn = "Test Brand A"; critique = "Headline fanger ikke i feedet. Skal poppe mere med stoerre font og hoejere kontrast." },
    @{ id = "kunde_b"; navn = "Test Brand B"; critique = "Baggrunden er for kedelig. Vil have mere stemning og blod gradient." },
    @{ id = "kunde_c"; navn = "Test Brand C"; critique = "Farverne er for moerke. Vil have mere lys og glans paa produktet." },
    @{ id = "kunde_d"; navn = "Test Brand D"; critique = "Produktet skal vaere stoerre og mere centralt. For meget tomhed omkring." },
    @{ id = "kunde_e"; navn = "Test Brand E"; critique = "Stemningen rammer ikke. For klinisk - vil have hyggeligere lys." }
)

$timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")

foreach ($c in $cases) {
    $stem = "$($c.id)_static_001"
    $sidecar = [ordered]@{
        kunde_id          = $c.id
        static_id         = "static_001"
        kunde_navn        = $c.navn
        critique          = $c.critique
        drive_folder_id   = "1dummy_drive_folder_$($c.id)"
        monday_item_id    = "9000000$([Math]::Abs($stem.GetHashCode()) % 100000)"
        submitted_at      = $timestamp
        iteration_number  = 1
    }
    $jsonPath = Join-Path $NeedsEditDir "$stem.json"
    $sidecar | ConvertTo-Json -Depth 10 | Set-Content -Path $jsonPath -Encoding UTF8
    Write-Host "Created: $jsonPath"
}

Write-Host "`nDone. Sidecar JSONs ready. Place corresponding image files (e.g. kunde_a_static_001.jpg) in same folder."