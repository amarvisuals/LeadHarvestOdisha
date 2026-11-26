# Run Backend PowerShell Script
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$ScriptDir\backend"

Write-Host ">>> Starting LeadHarvest Odisha Backend on port 8000..." -ForegroundColor Cyan

# Check if venv exists
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not detected. Creating with uv..." -ForegroundColor Yellow
    uv venv --python 3.11 .venv
    .\.venv\Scripts\activate
    uv pip install -r requirements.txt
}

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
