@echo off
cd /d "%~dp0"
title Gustee Setup

echo.
echo =============================================
echo  Gustee - Starting everything
echo =============================================
echo.


if exist ".venv\Scripts\pythonw.exe" (
    echo [1/5] Python venv found, skipping setup checks.
    goto deps_check
)

echo [1/5] Finding Python 3.9 - 3.12...
set PYTHON_CMD=

py -3.12 --version 2>nul 1>nul && set PYTHON_CMD=py -3.12
if defined PYTHON_CMD goto create_venv
py -3.11 --version 2>nul 1>nul && set PYTHON_CMD=py -3.11
if defined PYTHON_CMD goto create_venv
py -3.10 --version 2>nul 1>nul && set PYTHON_CMD=py -3.10
if defined PYTHON_CMD goto create_venv
py -3.9 --version 2>nul 1>nul && set PYTHON_CMD=py -3.9
if defined PYTHON_CMD goto create_venv

echo.
echo ERROR: Python 3.12 not found. MediaPipe requires Python 3.9 - 3.12.
echo Install from https://www.python.org/downloads/release/python-3128/
echo.
start "" "https://www.python.org/downloads/release/python-3128/"
pause
exit /b 1

:create_venv
for /f "tokens=*" %%v in ('%PYTHON_CMD% --version 2^>^&1') do echo Using %%v
echo [2/5] Creating virtual environment...
%PYTHON_CMD% -m venv .venv
if errorlevel 1 ( echo ERROR: Could not create venv. & pause & exit /b 1 )
if not exist ".venv\Scripts\pythonw.exe" ( echo ERROR: pythonw.exe missing. Delete .venv and retry. & pause & exit /b 1 )
echo .venv created

:deps_check
echo [3/5] Installing Python dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
if errorlevel 1 ( echo ERROR: pip install failed. & pause & exit /b 1 )
echo Python dependencies ready.

echo.
echo [4/5] Checking Node.js...
cd /d "%~dp0.."
node --version 2>nul 1>nul
if errorlevel 1 ( echo ERROR: Node.js not found. Get it from https://nodejs.org/ & pause & exit /b 1 )
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo Node %%v found.

echo.
echo [5/5] Installing Node dependencies...
if exist "node_modules" ( echo node_modules already exists, skipping & goto kill_old )
echo Running npm install, please wait...
npm install
if errorlevel 1 ( echo ERROR: npm install failed. & pause & exit /b 1 )

:kill_old
echo.
echo Stopping any previous Gustee companion on port 8765...
cd /d "%~dp0"
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":8765 "') do (
    if not "%%p"=="0" (
        taskkill /PID %%p /F >nul 2>&1
    )
)
timeout /t 2 /nobreak >nul

:launch
echo.
echo =============================================
echo  Launching Gustee...
echo =============================================
echo.

echo Starting Gustee companion...
echo NOTE: A small Gustee console window will appear - this is normal.
echo       Look for the Gustee tray icon after it starts.
cd /d "%~dp0"

:: Use python.exe (not pythonw.exe) in a minimized window so errors are visible
:: The tray icon will appear after the companion loads (about 5-10 seconds)
start "Gustee Companion" /MIN "%~dp0.venv\Scripts\python.exe" "%~dp0app.py"

echo Waiting for companion to start (loading PyTorch + MediaPipe)...
timeout /t 10 /nobreak >nul

:: Verify companion actually started on port 8765
netstat -ano | findstr ":8765 " >nul 2>&1
if errorlevel 1 (
    echo.
    echo  WARNING: Companion may not have started.
    echo  Check the minimized "Gustee Companion" window for errors.
    echo  Common fixes:
    echo    - Delete the .venv folder and run start.bat again
    echo    - Make sure no other app is using port 8765
    echo.
) else (
    echo  Companion is running on port 8765.
)

echo Starting web server on http://localhost:8080 ...
cd /d "%~dp0.."
start "Gustee Web" cmd /k "npm run dev"

timeout /t 5 /nobreak >nul
echo Opening browser...
start "" "http://localhost:8080"

echo.
echo =============================================
echo  Gustee is running!
echo.
echo  Web UI:    http://localhost:8080
echo  Database:  gustee (MongoDB Atlas)
echo  Companion: look for tray icon in taskbar
echo             (bottom-right, click ^ arrow)
echo.
echo  NEXT STEPS:
echo  1. Find the Gustee tray icon (bottom-right)
echo  2. Click it and choose "Show pairing key"
echo  3. In the web UI click "Connect device"
echo     and paste the pairing key
echo  4. Click "Allow camera access" in tray
echo.
echo  TIP: If no tray icon appears after 10s,
echo  check the minimized Gustee Companion window
echo  for error messages.
echo =============================================
echo.
pause
