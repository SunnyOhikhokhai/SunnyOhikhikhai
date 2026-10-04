@echo off
rem Run from a temporary copy, so that updating this file (git pull) while it
rem runs cannot disturb Windows reading it.
if /i not "%~1"=="--run" (
  copy /y "%~f0" "%TEMP%\nipam-start.bat" >nul
  call "%TEMP%\nipam-start.bat" --run "%~dp0"
  exit /b
)
set "ROOT=%~2"
title NIPAM - Starting up
cd /d "%ROOT%"
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

if exist "%ROOT%.git" (
  where git >nul 2>nul
  if not errorlevel 1 (
    echo  Checking for updates...
    git -C "%ROOT%." pull --ff-only
    if errorlevel 1 echo  Could not update - continuing with the current version.
  )
)

echo  [1/4] Preparing the backend (first run takes a few minutes)...
cd /d "%ROOT%backend"
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
cd /d "%ROOT%frontend"
call npm install --no-audit --no-fund --loglevel=error
if errorlevel 1 goto :failed

echo  [4/4] Starting NIPAM...
start "NIPAM backend - keep this window open" /d "%ROOT%backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"
start "NIPAM website - keep this window open" /d "%ROOT%frontend" cmd /k "npm run dev"

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
