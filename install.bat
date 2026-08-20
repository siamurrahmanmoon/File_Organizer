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
if exist "dist\AnimeOrganizerPro.exe" copy "dist\AnimeOrganizerPro.exe" "%INSTALL_DIR%\"
if exist "dist\AnimeOrganizerCLI.exe" copy "dist\AnimeOrganizerCLI.exe" "%INSTALL_DIR%\"
if exist "icon.ico" copy "icon.ico" "%INSTALL_DIR%\"

REM Create desktop shortcuts
echo [STEP 3] Creating desktop shortcuts...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\Anime Organizer Pro.lnk'); $s.TargetPath = '%INSTALL_DIR%\AnimeOrganizerPro.exe'; $s.IconLocation = '%INSTALL_DIR%\icon.ico'; $s.Save()"

REM Create start menu entry
echo [STEP 4] Creating Start Menu entry...
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
if not exist "%START_MENU%\Anime Organizer Pro" mkdir "%START_MENU%\Anime Organizer Pro"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%START_MENU%\Anime Organizer Pro\Anime Organizer Pro.lnk'); $s.TargetPath = '%INSTALL_DIR%\AnimeOrganizerPro.exe'; $s.IconLocation = '%INSTALL_DIR%\icon.ico'; $s.Save()"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%START_MENU%\Anime Organizer Pro\CLI Mode.lnk'); $s.TargetPath = '%INSTALL_DIR%\AnimeOrganizerCLI.exe'; $s.Save()"

echo.
echo ============================================================
echo   INSTALLATION COMPLETE!
echo ============================================================
echo.
echo   Installed to: %INSTALL_DIR%
echo   Desktop shortcut created!
echo   Start Menu entry created!
echo.
echo   You can now launch from:
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
