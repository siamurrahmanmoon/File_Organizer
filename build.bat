@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   Anime Organizer Pro - Windows EXE Builder
echo ============================================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate venv
call venv\Scripts\activate.bat

REM Check if PyInstaller is installed
where pyinstaller >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller==6.22.2
)

echo.
echo [STEP 1] Cleaning old builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo [STEP 2] Building GUI version (AnimeOrganizerPro.exe)...
echo        - Single file executable
echo        - No console window
echo        - Includes all dependencies
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "AnimeOrganizerPro" ^
    --icon "icon.ico" ^
    --clean ^
    organizer.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed! Check the error messages above.
    pause
    exit /b 1
)

echo.
echo [STEP 3] Building CLI version (AnimeOrganizerCLI.exe)...
echo        - Single file executable
echo        - Console window
echo        - Command line interface
echo.

pyinstaller ^
    --onefile ^
    --console ^
    --name "AnimeOrganizerCLI" ^
    --icon "icon.ico" ^
    --clean ^
    cli.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] CLI build failed! Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   BUILD SUCCESSFUL!
echo ============================================================
echo.
echo   Output files:
echo   - dist\AnimeOrganizerPro.exe  (GUI Version)
echo   - dist\AnimeOrganizerCLI.exe  (CLI Version)
echo.
echo   You can now distribute these files to other Windows PCs.
echo   No Python installation required on target machines!
echo ============================================================
echo.

REM Open the dist folder
explorer dist

pause
