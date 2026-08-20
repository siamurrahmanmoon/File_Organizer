@echo off
setlocal
cd /d "%~dp0"

title Anime Organizer Pro - CLI
color 0B

echo ============================================================
echo   Anime Organizer Pro - CLI Mode
echo ============================================================
echo.
echo   Usage:
echo     run_cli.bat -s "Source Folder" -o "Output Folder"
echo     run_cli.bat --execute -s "R:\Anime" -o "R:\Organized"
echo     run_cli.bat --list-profiles
echo     run_cli.bat --help
echo.
echo ============================================================
echo.

REM Check if EXE exists (pre-built version)
if exist "dist\AnimeOrganizerCLI.exe" (
    echo [INFO] Launching pre-built EXE version...
    echo.
    "dist\AnimeOrganizerCLI.exe" %*
) else if exist "venv\Scripts\python.exe" (
    echo [INFO] Launching with Python (venv)...
    echo.
    "venv\Scripts\python.exe" cli.py %*
) else (
    echo [WARNING] venv not found, falling back to system Python...
    echo.
    python cli.py %*
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Command exited with error code %ERRORLEVEL%.
    echo.
    pause
)
