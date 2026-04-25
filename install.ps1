param()

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogPath = Join-Path $Root "_install.log"

function Write-Log($Message) {
    $Line = "$(Get-Date -Format o) $Message"
    Add-Content -LiteralPath $LogPath -Value $Line
    Write-Host $Message
}

try {
    Write-Log "Project Atlas install started."

    $Python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $Python) {
        throw "Python was not found. Install Python 3.12 or newer, then run install.ps1 again."
    }

    $Npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $Npm) {
        throw "npm was not found. Install Node.js, then run install.ps1 again."
    }

    $VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        Write-Log "Creating local Python environment."
        & python -m venv (Join-Path $Root ".venv") 2>&1 | Add-Content -LiteralPath $LogPath
    }

    Write-Log "Installing backend."
    & $VenvPython -m pip install -q -e $Root 2>&1 | Add-Content -LiteralPath $LogPath

    Write-Log "Installing dashboard."
    Push-Location (Join-Path $Root "dashboard")
    try {
        & npm install --silent 2>&1 | Add-Content -LiteralPath $LogPath
    } finally {
        Pop-Location
    }

    Write-Log "Install complete. Run start.ps1 next."
} catch {
    Write-Log "Install failed: $($_.Exception.Message)"
    Write-Host "Project Atlas install failed: $($_.Exception.Message)"
    exit 1
}