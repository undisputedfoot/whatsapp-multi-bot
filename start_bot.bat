@echo off
title WhatsApp Bot - Keep This Window Open
cd /d "%~dp0"
cls
echo ==============================================
echo     WHATSAPP BOT - Keep This Window Open!
echo ==============================================
echo.
echo    Your bot is starting...
echo.
echo    A browser will open shortly.
echo    Login: admin
echo    Password: admin123
echo.
echo    DO NOT CLOSE THIS WINDOW
echo    The bot only works while this is open.
echo ==============================================
echo.
:: Auto-open the dashboard in the default browser
start "" http://localhost:5000
python main.py
pause
