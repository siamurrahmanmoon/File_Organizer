@echo off
setlocal
cd /d "%~dp0"

title Anime Organizer Pro - Distribution Package Builder
color 0A

echo ============================================================
echo   Anime Organizer Pro - Distribution Package Builder
echo ============================================================
echo.

REM Check if EXEs exist
if not exist "dist\AnimeOrganizerPro.exe" (
    echo [ERROR] EXE files not found!
    echo Please run setup_and_build.bat first.
    pause
    exit /b 1
)

REM Create distribution folder
set "PKG_NAME=AnimeOrganizerPro_v4.1"
set "PKG_DIR=R:\%PKG_NAME%"

echo [STEP 1] Creating distribution folder...
if exist "%PKG_DIR%" rmdir /s /q "%PKG_DIR%"
mkdir "%PKG_DIR%"

echo [STEP 2] Copying files...
copy /Y "dist\AnimeOrganizerPro.exe" "%PKG_DIR%\" >nul
echo        + AnimeOrganizerPro.exe
copy /Y "dist\AnimeOrganizerCLI.exe" "%PKG_DIR%\" >nul
echo        + AnimeOrganizerCLI.exe
copy /Y "icon.ico" "%PKG_DIR%\" >nul
echo        + icon.ico
xcopy /Y /E "presets" "%PKG_DIR%\presets\" >nul 2>nul
echo        + presets folder

echo [STEP 3] Creating Install.bat...

REM Write Install.bat directly
(
echo @echo off
echo setlocal
echo cd /d "%%~dp0"
echo.
echo title Anime Organizer Pro - Installer
echo color 0A
echo.
echo echo ============================================================
echo echo   Anime Organizer Pro - Installer
echo echo ============================================================
echo echo.
echo.
echo set "INSTALL_DIR=%%USERPROFILE%%\AnimeOrganizerPro"
echo echo Installing to: %%INSTALL_DIR%%
echo.
echo if not exist "%%INSTALL_DIR%%" mkdir "%%INSTALL_DIR%%"
echo.
echo echo Copying files...
echo copy /Y "AnimeOrganizerPro.exe" "%%INSTALL_DIR%%\" ^>nul
echo copy /Y "AnimeOrganizerCLI.exe" "%%INSTALL_DIR%%\" ^>nul
echo copy /Y "icon.ico" "%%INSTALL_DIR%%\" ^>nul
echo xcopy /Y /E "presets" "%%INSTALL_DIR%%\presets\" ^>nul 2^>nul
echo echo Done!
echo.
echo echo.
echo echo Creating desktop shortcuts...
echo powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), 'Anime Organizer Pro.lnk')); $s.TargetPath = '%%INSTALL_DIR%%\AnimeOrganizerPro.exe'; $s.WorkingDirectory = '%%INSTALL_DIR%%'; $s.Save()"
echo powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), 'Anime Organizer CLI.lnk')); $s.TargetPath = '%%INSTALL_DIR%%\AnimeOrganizerCLI.exe'; $s.WorkingDirectory = '%%INSTALL_DIR%%'; $s.Save()"
echo echo Done!
echo.
echo echo ============================================================
echo echo   INSTALLATION COMPLETE!
echo echo ============================================================
echo echo.
echo echo   Installed to: %%INSTALL_DIR%%
echo echo   Desktop shortcuts created!
echo echo.
echo echo ============================================================
echo echo.
echo set /p LAUNCH="Launch now? (Y/N): "
echo if /i "%%LAUNCH%%"=="Y" start "" "%%INSTALL_DIR%%\AnimeOrganizerPro.exe"
echo pause
) > "%PKG_DIR%\Install.bat"

echo        + Install.bat created

echo [STEP 4] Creating README.txt...
(
echo Anime Organizer Pro v4.1
echo ========================
echo.
echo QUICK START:
echo   1. Run Install.bat
echo   2. Use Desktop shortcuts to launch
echo.
echo FILES:
echo   AnimeOrganizerPro.exe - GUI Application
echo   AnimeOrganizerCLI.exe - Command Line Version
echo   Install.bat - Installer
echo.
echo FEATURES:
echo   - Smart file renaming
echo   - Duplicate detection
echo   - Custom templates
echo   - Batch processing
echo   - Rollback support
echo.
echo System: Windows 10/11, 4GB RAM
) > "%PKG_DIR%\README.txt"

echo        + README.txt created

echo.
echo ============================================================
echo   DONE!
echo ============================================================
echo.
echo   Location: %PKG_DIR%
echo.
echo   Contents:
dir /b "%PKG_DIR%"
echo.
echo   To install on another PC:
echo   1. Copy entire folder
echo   2. Run Install.bat
echo.
explorer "%PKG_DIR%"
pause
