@echo off
title NIPAM - Starting up
cd /d "%~dp0"
echo.
echo  ==========================================
echo    NIPAM - starting the platform
echo  ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo  Python is not installed.
  echo  Install it from https://www.python.org/downloads/
  echo  IMPORTANT: tick "Add python.exe to PATH" during installation.
  echo  Then double-click START-NIPAM.bat again.
  pause
  exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo  Node.js is not installed.
  echo  Install the LTS version from https://nodejs.org
  echo  Then double-click START-NIPAM.bat again.
  pause
  exit /b 1
)

echo  [1/4] Preparing the backend (first run takes a few minutes)...
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 goto :failed
)
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 goto :failed

echo  [2/4] Preparing the database and content...
".venv\Scripts\python.exe" -m app.seed --create-tables --demo --aduda
if errorlevel 1 goto :failed

echo  [3/4] Preparing the website (first run takes a few minutes)...
cd /d "%~dp0frontend"
if not exist "node_modules" (
  call npm install --no-audit --no-fund
  if errorlevel 1 goto :failed
)

echo  [4/4] Starting NIPAM...
start "NIPAM backend - keep this window open" /d "%~dp0backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"
start "NIPAM website - keep this window open" /d "%~dp0frontend" cmd /k "npm run dev"

echo.
echo  Opening http://localhost:5173 in your browser...
timeout /t 8 /nobreak >nul
start "" http://localhost:5173

echo.
echo  NIPAM is running. Two windows are open - keep them open while you use the site.
echo  To stop NIPAM, close those two windows.
echo.
echo  Admin login:  admin@nipam.local  /  ChangeMe!Admin2026
echo  Member login: member@nipam.local  /  Member!Demo2026
echo.
pause
exit /b 0

:failed
echo.
echo  Something went wrong. Take a screenshot of this window and send it to Claude.
pause
exit /b 1
