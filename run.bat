@echo off
setlocal
cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    echo [INFO] Launching with project virtual environment (venv)...
    "venv\Scripts\python.exe" organizer.py %*
) else (
    echo [WARNING] venv not found, falling back to system python...
    python organizer.py %*
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with error code %ERRORLEVEL%.
    pause
)
