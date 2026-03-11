@echo off
REM ================================================================
REM Meeting Transcriber Pro - GUI Launcher
REM ================================================================
REM This script launches the modern GUI application for meeting
REM transcription with audio recording, transcription, and summarization.
REM ================================================================

TITLE Meeting Transcriber Pro - GUI

echo.
echo ============================================================
echo      Meeting Transcriber Pro - GUI Application
echo ============================================================
echo.

REM Check if Python is available
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Navigate to script directory
cd /d "%~dp0"

REM Check for virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo NOTE: No virtual environment found. Using system Python.
    echo       Run setup.bat first to create a virtual environment.
    echo.
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import customtkinter" 2>nul
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt -q
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
)

REM Check for .env file
if not exist ".env" (
    if exist ".env.example" (
        echo.
        echo WARNING: No .env file found!
        echo Please copy .env.example to .env and add your API keys.
        echo.
    )
)

echo.
echo Starting Meeting Transcriber Pro GUI...
echo.

REM Launch the GUI application
python -m src.gui_app

REM Check for errors
if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERROR: Application exited with an error.
    echo ============================================================
    pause
)
