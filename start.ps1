param()

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$AtlasDir = Join-Path $Root ".atlas"
$LogPath = Join-Path $Root "_start.log"
New-Item -ItemType Directory -Force -Path $AtlasDir | Out-Null

function Write-Log($Message) {
    $Line = "$(Get-Date -Format o) $Message"
    Add-Content -LiteralPath $LogPath -Value $Line
    Write-Host $Message
}

function Test-Port($Port) {
    $Connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $Connection
}

try {
    Write-Log "Project Atlas start requested."

    $Python = Join-Path $Root ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $Python)) {
        $Python = "python"
    }

    if (-not (Test-Port 8765)) {
        Write-Log "Starting backend on http://127.0.0.1:8765"
        Start-Process -FilePath $Python -ArgumentList @("-m", "atlas_backend.cli", "serve", "--port", "8765") -WorkingDirectory $Root -RedirectStandardOutput (Join-Path $AtlasDir "_backend.log") -RedirectStandardError (Join-Path $AtlasDir "_backend.err.log") -WindowStyle Hidden | Out-Null
    } else {
        Write-Log "Backend already running on http://127.0.0.1:8765"
    }

    if (-not (Test-Port 5177)) {
        Write-Log "Starting dashboard on http://127.0.0.1:5177"
        Start-Process -FilePath "npm.cmd" -ArgumentList @("run", "dev") -WorkingDirectory (Join-Path $Root "dashboard") -RedirectStandardOutput (Join-Path $AtlasDir "_dashboard.log") -RedirectStandardError (Join-Path $AtlasDir "_dashboard.err.log") -WindowStyle Hidden | Out-Null
    } else {
        Write-Log "Dashboard already running on http://127.0.0.1:5177"
    }

    Write-Log "Open http://127.0.0.1:5177"
    Write-Host "Open Project Atlas: http://127.0.0.1:5177"
} catch {
    Write-Log "Start failed: $($_.Exception.Message)"
    Write-Host "Project Atlas start failed: $($_.Exception.Message)"
    exit 1
}