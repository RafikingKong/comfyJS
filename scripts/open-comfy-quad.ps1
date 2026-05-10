<#
    Opens 4 Chrome app-mode windows positioned in screen quadrants.
    Each window points to a different ComfyUI instance port (8001-8004).
    Requires Chrome installed and 4 ComfyUI processes running on those ports.
#>
Add-Type -AssemblyName System.Windows.Forms
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$hw = [Math]::Floor($screen.Width / 2)
$hh = [Math]::Floor($screen.Height / 2)

$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chrome)) {
    $chrome = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
}
if (-not (Test-Path $chrome)) {
    Write-Host "Chrome not found. Install Chrome or edit script with your browser path."
    exit 1
}

$instances = @(
    @{ port = 8001; x = 0;   y = 0;   name = "chain1" },
    @{ port = 8002; x = $hw; y = 0;   name = "chain2" },
    @{ port = 8003; x = 0;   y = $hh; name = "chain3" },
    @{ port = 8004; x = $hw; y = $hh; name = "chain4" }
)

foreach ($i in $instances) {
    $url = "http://127.0.0.1:$($i.port)"
    $userDir = "$env:TEMP\chrome-comfy-$($i.name)"
    Start-Process -FilePath $chrome -ArgumentList @(
        "--app=$url",
        "--window-position=$($i.x),$($i.y)",
        "--window-size=$hw,$hh",
        "--user-data-dir=`"$userDir`""
    )
    Start-Sleep -Milliseconds 500
}

Write-Host "Opened 4 ComfyUI windows in screen quadrants."