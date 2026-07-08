@echo off
title WhatsApp Multi-Bot - Engine Setup
cd /d "%~dp0"

echo ========================================
echo  WhatsApp Multi-Bot - Engine Setup
echo ========================================
echo.

:: Check for Node.js
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [1/3] Downloading Node.js...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://nodejs.org/dist/v22.14.0/node-v22.14.0-x64.msi' -OutFile '%TEMP%\node-install.msi' -UseBasicParsing}"
    echo Installing Node.js...
    start /wait msiexec /i "%TEMP%\node-install.msi" /quiet
    echo Node.js installed!
) else (
    echo [1/3] Node.js found: OK
)

:: Install npm deps
echo [2/3] Installing WhatsApp engine dependencies...
cd wa-engine
call npm install --production
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: npm install failed
    pause
    exit /b 1
)
echo Dependencies installed!

:: Check Python
echo [3/3] Checking Python setup...
cd ..
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Python not found in PATH
    echo Make sure Python is installed and in your PATH
)

echo.
echo ========================================
echo  Setup complete! Starting the bot...
echo ========================================
echo.
echo  Open http://localhost:5000 in your browser
echo  Login: admin / admin123
echo.

:: Start the bot
python main.py
pause
