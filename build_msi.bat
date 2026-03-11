@echo off
REM ================================================================
REM Meeting Transcriber Pro - MSI Build Script
REM ================================================================
REM Produces:  dist\MeetingTranscriber.msi
REM
REM Prerequisites (must be installed before running):
REM   1. Python 3.8+  in PATH  (https://www.python.org/)
REM   2. WiX Toolset v4        (winget install WiXToolset.WiX)
REM   3. .NET 6+ SDK           (winget install Microsoft.DotNet.SDK.8)
REM   FFmpeg is downloaded automatically by this script.
REM ================================================================

TITLE Meeting Transcriber Pro - MSI Builder
SETLOCAL ENABLEDELAYEDEXPANSION

cd /d "%~dp0"

echo.
echo ============================================================
echo   Meeting Transcriber Pro - MSI Build Pipeline
echo ============================================================
echo.

REM ----------------------------------------------------------------
REM SECURITY CHECK: Abort if .env contains a real API key
REM ----------------------------------------------------------------
echo [0/6] Security check – ensuring .env is excluded...

if exist ".env" (
    findstr /i /c:"your_openai_api_key_here" ".env" >nul 2>&1
    if errorlevel 1 (
        REM The placeholder text was NOT found, meaning a real key is set
        echo.
        echo *** SECURITY NOTICE ***
        echo A .env file with what appears to be a real API key was detected.
        echo It will NOT be included in the package - this is correct behaviour.
        echo Only .env.example ^(template with placeholder values^) is bundled.
        echo *** The build will continue safely. ***
        echo.
    )
)

REM Explicitly verify .env is never in the dist folder (post-build guard runs later)
echo       .env exclusion guard: ACTIVE
echo.

REM ----------------------------------------------------------------
REM STEP 1: Verify prerequisites
REM ----------------------------------------------------------------
echo [1/6] Checking prerequisites...

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH.
    goto :fail
)

where wix >nul 2>&1
if errorlevel 1 (
    echo ERROR: WiX Toolset v4 (wix.exe) not found in PATH.
    echo        Install with:  winget install WiXToolset.WiX
    goto :fail
)

echo       Python  : OK
echo       WiX v4  : OK
echo.

REM ----------------------------------------------------------------
REM STEP 2: Download / verify FFmpeg
REM ----------------------------------------------------------------
echo [2/6] Checking FFmpeg...

if exist "ffmpeg\ffmpeg.exe" (
    echo       FFmpeg already present in ffmpeg\ folder. Skipping download.
) else (
    echo       FFmpeg not found. Attempting to download...
    if not exist "ffmpeg" mkdir ffmpeg

    REM --- Try winget first (Windows 10 1709+ / Windows 11) ---
    where winget >nul 2>&1
    if not errorlevel 1 (
        echo       Trying winget install ffmpeg...
        winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
        REM winget installs ffmpeg to PATH but not the local folder; copy if found
        where ffmpeg >nul 2>&1
        if not errorlevel 1 (
            for /f "delims=" %%F in ('where ffmpeg') do (
                copy "%%F" "ffmpeg\ffmpeg.exe" >nul 2>&1
            )
        )
        where ffprobe >nul 2>&1
        if not errorlevel 1 (
            for /f "delims=" %%F in ('where ffprobe') do (
                copy "%%F" "ffmpeg\ffprobe.exe" >nul 2>&1
            )
        )
    )

    REM --- Fallback: download a static FFmpeg build via PowerShell ---
    if not exist "ffmpeg\ffmpeg.exe" (
        echo       winget unavailable or did not place ffmpeg locally.
        echo       Downloading static FFmpeg build via PowerShell...
        powershell -NoProfile -ExecutionPolicy Bypass -Command ^
            "$ProgressPreference='SilentlyContinue'; " ^
            "$url='https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip'; " ^
            "$zip='ffmpeg_dl.zip'; " ^
            "Invoke-WebRequest -Uri $url -OutFile $zip; " ^
            "Expand-Archive -Path $zip -DestinationPath 'ffmpeg_tmp' -Force; " ^
            "$bin = Get-ChildItem 'ffmpeg_tmp' -Recurse -Filter 'ffmpeg.exe' | Select-Object -First 1; " ^
            "Copy-Item $bin.FullName 'ffmpeg\ffmpeg.exe'; " ^
            "$bin2 = Get-ChildItem 'ffmpeg_tmp' -Recurse -Filter 'ffprobe.exe' | Select-Object -First 1; " ^
            "Copy-Item $bin2.FullName 'ffmpeg\ffprobe.exe'; " ^
            "Remove-Item $zip -Force; " ^
            "Remove-Item 'ffmpeg_tmp' -Recurse -Force"
        if errorlevel 1 (
            echo ERROR: FFmpeg download failed. Check your internet connection.
            goto :fail
        )
    )

    if not exist "ffmpeg\ffmpeg.exe" (
        echo ERROR: FFmpeg binaries not found after download attempt.
        goto :fail
    )
    echo       FFmpeg downloaded successfully.
)

echo       FFmpeg : OK  ^(ffmpeg\ffmpeg.exe^)
echo.

REM ----------------------------------------------------------------
REM STEP 3: Create / activate virtual environment
REM ----------------------------------------------------------------
echo [3/6] Setting up Python environment...

if not exist "venv\Scripts\activate.bat" (
    echo       Creating virtual environment...
    python -m venv venv
    if errorlevel 1 goto :fail
)

call venv\Scripts\activate.bat

echo       Installing / updating dependencies...
pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install pyinstaller -q
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies.
    goto :fail
)
echo       Dependencies: OK
echo.

REM ----------------------------------------------------------------
REM STEP 4: PyInstaller – bundle app into dist\MeetingTranscriber\
REM ----------------------------------------------------------------
echo [4/6] Running PyInstaller...

if exist "dist\MeetingTranscriber" (
    echo       Removing old PyInstaller output...
    rmdir /s /q "dist\MeetingTranscriber"
)
if exist "build" (
    rmdir /s /q "build"
)

pyinstaller MeetingTranscriber.spec --noconfirm
if errorlevel 1 (
    echo ERROR: PyInstaller build failed. See output above.
    goto :fail
)

REM --- Post-build safety check: ensure .env never made it into dist ---
if exist "dist\MeetingTranscriber\.env" (
    echo ERROR: .env was found inside the PyInstaller output! Deleting it now.
    del /f /q "dist\MeetingTranscriber\.env"
    echo       .env removed from dist. Review MeetingTranscriber.spec datas list.
)

echo       PyInstaller: OK  ^(dist\MeetingTranscriber\^)
echo.

REM ----------------------------------------------------------------
REM STEP 5: Harvest PyInstaller output directory with WiX
REM         Generates installer\AppFiles.wxs with all bundled files
REM ----------------------------------------------------------------
echo [5/6] Harvesting application files for WiX...

if not exist "installer" mkdir installer

wix harvest dir "dist\MeetingTranscriber" ^
    -cg HarvestedAppFiles ^
    -dr INSTALLFOLDER ^
    -var var.SourceDir ^
    -nologo ^
    -out "installer\AppFiles.wxs"

if errorlevel 1 (
    echo ERROR: wix harvest failed.
    goto :fail
)
echo       Harvest: OK  ^(installer\AppFiles.wxs^)
echo.

REM ----------------------------------------------------------------
REM STEP 6: Build the MSI
REM ----------------------------------------------------------------
echo [6/6] Building MSI...

if not exist "dist" mkdir dist

wix build ^
    "installer\MeetingTranscriber.wxs" ^
    "installer\AppFiles.wxs" ^
    -d SourceDir="dist\MeetingTranscriber" ^
    -ext WixToolset.UI.wixext ^
    -nologo ^
    -o "dist\MeetingTranscriber.msi"

if errorlevel 1 (
    echo ERROR: WiX MSI build failed. See output above.
    goto :fail
)

echo.
echo ============================================================
echo   BUILD SUCCEEDED
echo   Output: dist\MeetingTranscriber.msi
echo ============================================================
echo.
echo Next steps:
echo   1. Copy dist\MeetingTranscriber.msi to target machine
echo   2. Double-click to install (or: msiexec /i MeetingTranscriber.msi)
echo   3. After install, find .env.example in the install directory,
echo      copy it to .env, and set your OPENAI_API_KEY value.
echo      Default install path:
echo        C:\Program Files\Meeting Transcriber Pro\
echo.
goto :end

:fail
echo.
echo ============================================================
echo   BUILD FAILED  -  check errors above
echo ============================================================
pause
exit /b 1

:end
pause
