@echo off
echo ========================================
echo Meeting Transcriber (Simple Mode)
echo ========================================
echo.
echo Running in SIMPLE mode (microphone only)
echo.

REM Check if virtual environment exists
if not exist venv (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo WARNING: .env file not found!
    echo Please copy .env.example to .env and configure your API keys.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run in simple mode
echo Starting Meeting Transcriber in Simple Mode...
echo.
python -m src.main --simple

REM Deactivate when done
deactivate
echo.
pause
