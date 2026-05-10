<#
    Starts N ComfyUI processes on different ports (8001-8005).
    For multi-instance setup enabling true parallel chain execution.

    PREREQ: ComfyUI installed as standalone (not just Desktop). Adjust $comfyMain to your install.
    Each instance shares custom_nodes/, models/, and (optionally) output/ via shared filesystem.
#>
param(
    [int]$InstanceCount = 5,
    [int]$BasePort = 8001,
    [string]$ComfyMain = "C:\path\to\ComfyUI\main.py"
)

if (-not (Test-Path $ComfyMain)) {
    Write-Host "ERROR: ComfyUI main.py not found at $ComfyMain"
    Write-Host "Edit -ComfyMain parameter to point to your ComfyUI install."
    exit 1
}

for ($i = 0; $i -lt $InstanceCount; $i++) {
    $port = $BasePort + $i
    Write-Host "Starting ComfyUI instance on port $port"
    Start-Process -FilePath "python" -ArgumentList @(
        "`"$ComfyMain`"",
        "--port", "$port",
        "--listen", "127.0.0.1"
    ) -WindowStyle Minimized
    Start-Sleep -Seconds 2
}

Write-Host "`n$InstanceCount ComfyUI instances starting. Each window minimized."
Write-Host "Open in browser: http://127.0.0.1:$BasePort through http://127.0.0.1:$($BasePort + $InstanceCount - 1)"
Write-Host "Or run open-comfy-quad.ps1 for quadrant layout."