@echo off
echo ========================================
echo Meeting Transcriber - Windows Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Python found!
python --version
echo.

REM Create virtual environment
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists.
) else (
    python -m venv venv
    echo Virtual environment created.
)
echo.

REM Activate virtual environment
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Upgrade pip
echo [4/5] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo [5/5] Installing dependencies...
pip install -r requirements.txt
echo.

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo ========================================
    echo IMPORTANT: Configure your API keys!
    echo ========================================
    echo Please edit the .env file and add your:
    echo   - OPENAI_API_KEY
    echo.
    echo You can get your OpenAI API key from:
    echo https://platform.openai.com/api-keys
    echo.
)

echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo To run the application:
echo   1. Make sure you've configured .env with your API keys
echo   2. Run: venv\Scripts\activate.bat
echo   3. Run: python -m src.main
echo.
echo For simple mode (microphone only):
echo   python -m src.main --simple
echo.
echo To list available audio devices:
echo   python -m src.main --list-devices
echo.
pause
