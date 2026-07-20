$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (Get-Command py -ErrorAction SilentlyContinue) {
    py server.py --sync
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python server.py --sync
} else {
    Write-Host "Python was not found. Install Python 3 from python.org, then reopen PowerShell." -ForegroundColor Red
    exit 1
}
