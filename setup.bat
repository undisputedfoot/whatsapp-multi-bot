@echo off
title WhatsApp Multi-Bot Setup
cls
echo ============================================
echo   🤖 WhatsApp Multi-Bot - Quick Setup
echo ============================================
echo.
echo This will install everything you need.
echo.

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [1/4] Installing Python...
    :: Try winget first (Windows 10/11)
    winget install --id Python.Python.3.12 --silent --accept-package-agreements >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo Could not install Python automatically.
        echo Please download Python 3.12 from: https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
    echo ✅ Python installed!
) else (
    echo [1/4] Python found ✅
)

:: Install required packages
echo [2/4] Installing required packages...
python -m pip install --upgrade pip -q
python -m pip install playwright httpx flask flask-socketio flask-cors python-dotenv gunicorn eventlet Pillow requests emoji sqlite-utils -q
echo ✅ Packages installed!

:: Install Chromium for Playwright
echo [3/4] Installing Chromium browser (this may take a few minutes)...
python -m playwright install chromium
echo ✅ Chromium installed!

:: Create .env from template if missing
echo [4/4] Setting up configuration...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo ✅ Created .env file from template
    echo.
    echo ⚠️  Open .env to customize your settings:
    echo    - Add your AI API keys
    echo    - Change session names
    echo    - Set your language
) else (
    echo ✅ .env already exists
)

echo.
echo ============================================
echo   ✅ Setup Complete!
echo ============================================
echo.
echo To start the bot, double-click:  start_bot.bat
echo Or run:  python main.py
echo.
echo Then open:  http://localhost:5000
echo Login: admin / admin123
echo.
pause
