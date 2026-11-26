@echo off
title LeadHarvest Odisha - One-Click Launcher
echo ========================================================
echo   LeadHarvest Odisha - One-Click Lead Data Collector
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/2] Starting Python FastAPI Backend on http://127.0.0.1:8000 ...
start "LeadHarvest Backend" powershell -NoExit -ExecutionPolicy Bypass -File "%~dp0run-backend.ps1"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Next.js Frontend on http://localhost:3000 ...
start "LeadHarvest Frontend" powershell -NoExit -ExecutionPolicy Bypass -File "%~dp0run-frontend.ps1"

timeout /t 4 /nobreak >nul
echo.
echo Opening http://localhost:3000 in your browser...
start http://localhost:3000

echo.
echo LeadHarvest Odisha is now running!
echo Keep the backend and frontend terminal windows open.
pause
