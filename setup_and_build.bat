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

REM Step 3: Build GUI EXE
echo [STEP 3] Building GUI EXE (AnimeOrganizerPro.exe)...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "AnimeOrganizerPro" ^
    --icon "icon.ico" ^
    --clean ^
    organizer.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] GUI build failed!
    pause
    exit /b 1
)
echo [OK] GUI EXE built successfully.
echo.

REM Step 4: Build CLI EXE
echo [STEP 4] Building CLI EXE (AnimeOrganizerCLI.exe)...
pyinstaller ^
    --onefile ^
    --console ^
    --name "AnimeOrganizerCLI" ^
    --icon "icon.ico" ^
    --clean ^
    cli.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] CLI build failed!
    pause
    exit /b 1
)
echo [OK] CLI EXE built successfully.
echo.

echo ============================================================
echo   SETUP COMPLETE!
echo ============================================================
echo.
echo   Output files:
echo   - dist\AnimeOrganizerPro.exe  (GUI Version)
echo   - dist\AnimeOrganizerCLI.exe  (CLI Version)
echo.
echo   To run GUI:  Double-click run.bat
echo   To run CLI:  Double-click run_cli.bat
echo   To install:  Double-click install.bat
echo.
echo ============================================================
echo.

explorer dist
pause
