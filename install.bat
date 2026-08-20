@echo off
setlocal
cd /d "%~dp0"

title Anime Organizer Pro - Installer
color 09

echo ============================================================
echo   Anime Organizer Pro - Windows Installer
echo ============================================================
echo.
echo   This will install Anime Organizer Pro on your system.
echo.
echo ============================================================
echo.

REM Check if running as admin
net session >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

REM Create installation directory
set "INSTALL_DIR=C:\Program Files\AnimeOrganizerPro"
echo [STEP 1] Creating installation directory: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy files
echo [STEP 2] Copying files...
if exist "dist\AnimeOrganizerPro.exe" (
    copy /Y "dist\AnimeOrganizerPro.exe" "%INSTALL_DIR%\" >nul
    echo        - AnimeOrganizerPro.exe copied
)
if exist "dist\AnimeOrganizerCLI.exe" (
    copy /Y "dist\AnimeOrganizerCLI.exe" "%INSTALL_DIR%\" >nul
    echo        - AnimeOrganizerCLI.exe copied
)
if exist "icon.ico" (
    copy /Y "icon.ico" "%INSTALL_DIR%\" >nul
    echo        - icon.ico copied
)

REM Create desktop shortcuts using PowerShell (simplified)
echo [STEP 3] Creating desktop shortcuts...

REM Create GUI shortcut
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; ^
     $s = $ws.CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), 'Anime Organizer Pro.lnk')); ^
     $s.TargetPath = 'C:\Program Files\AnimeOrganizerPro\AnimeOrganizerPro.exe'; ^
     $s.WorkingDirectory = 'C:\Program Files\AnimeOrganizerPro'; ^
     $s.Description = 'Anime Organizer Pro - GUI'; ^
     $s.Save()"

if %ERRORLEVEL% EQU 0 (
    echo        - Desktop shortcut created
) else (
    echo        - Desktop shortcut failed (non-critical)
)

REM Create Start Menu folder
echo [STEP 4] Creating Start Menu entry...
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "SM_FOLDER=%START_MENU%\Anime Organizer Pro"
if not exist "%SM_FOLDER%" mkdir "%SM_FOLDER%"

REM Create GUI shortcut in Start Menu
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; ^
     $s = $ws.CreateShortcut('%SM_FOLDER%\Anime Organizer Pro.lnk'); ^
     $s.TargetPath = 'C:\Program Files\AnimeOrganizerPro\AnimeOrganizerPro.exe'; ^
     $s.WorkingDirectory = 'C:\Program Files\AnimeOrganizerPro'; ^
     $s.Description = 'Anime Organizer Pro - GUI'; ^
     $s.Save()"

REM Create CLI shortcut in Start Menu
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; ^
     $s = $ws.CreateShortcut('%SM_FOLDER%\CLI Mode.lnk'); ^
     $s.TargetPath = 'C:\Program Files\AnimeOrganizerPro\AnimeOrganizerCLI.exe'; ^
     $s.WorkingDirectory = 'C:\Program Files\AnimeOrganizerPro'; ^
     $s.Description = 'Anime Organizer Pro - CLI'; ^
     $s.Save()"

echo        - Start Menu entries created

echo.
echo ============================================================
echo   INSTALLATION COMPLETE!
echo ============================================================
echo.
echo   Installed to: %INSTALL_DIR%
echo.
echo   Installed files:
dir /b "%INSTALL_DIR%"
echo.
echo   Launch from:
echo   - Desktop shortcut
echo   - Start Menu > Anime Organizer Pro
echo   - Direct: %INSTALL_DIR%\AnimeOrganizerPro.exe
echo.
echo ============================================================
echo.

REM Launch the app
set /p LAUNCH="Launch Anime Organizer Pro now? (Y/N): "
if /i "%LAUNCH%"=="Y" (
    start "" "%INSTALL_DIR%\AnimeOrganizerPro.exe"
)

pause
