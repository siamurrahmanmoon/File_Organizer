@echo off
setlocal
cd /d "%~dp0"

title Anime Organizer Pro - GUI
color 0A

echo ============================================================
echo   Anime Organizer Pro - GUI Launcher
echo ============================================================
echo.

REM Check if EXE exists (pre-built version)
if exist "dist\AnimeOrganizerPro.exe" (
    echo [INFO] Launching pre-built EXE version...
    echo.
    start "" "dist\AnimeOrganizerPro.exe"
    exit /b 0
)

REM Check if venv exists for Python version
if exist "venv\Scripts\python.exe" (
    echo [INFO] Launching with Python (venv)...
    echo.
    "venv\Scripts\python.exe" organizer.py %*
) else (
    echo [WARNING] venv not found, falling back to system Python...
    echo.
    python organizer.py %*
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================
    echo [ERROR] Application exited with error code %ERRORLEVEL%.
    echo ============================================================
    echo.
    pause
)
