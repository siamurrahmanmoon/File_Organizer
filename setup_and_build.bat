@echo off
setlocal
cd /d "%~dp0"

title Anime Organizer Pro - Setup & Build
color 0D

echo ============================================================
echo   Anime Organizer Pro - Full Setup & Build
echo ============================================================
echo.

REM Step 1: Create virtual environment
if not exist "venv\Scripts\python.exe" (
    echo [STEP 1] Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [STEP 1] Virtual environment already exists. Skipping...
)
echo.

REM Step 2: Activate and install dependencies
echo [STEP 2] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)
echo [OK] Dependencies installed.
echo.

REM Step 3: Build EXE
echo [STEP 3] Building Windows EXE files...
echo.
call build.bat

echo.
echo ============================================================
echo   SETUP COMPLETE!
echo ============================================================
echo.
echo   To run GUI:  Double-click run.bat
echo   To run CLI:  Double-click run_cli.bat
echo   To rebuild:  Double-click build.bat
echo.
echo ============================================================
pause
