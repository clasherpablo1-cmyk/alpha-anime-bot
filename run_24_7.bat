@echo off
chcp 65001 > nul
title Alpha Anime Bot - 24/7 Supervisor Mode (@Alpha_animelar_bot)
color 0B

echo =====================================================================
echo       ALPHA ANIME TELEGRAM BOT -- 24/7 SUPERVISOR WATCHDOG
echo =====================================================================
echo.
echo  * Rasmiy Bot:    @Alpha_animelar_bot
echo  * Rasmiy Kanal:  @uzbekcha_animelar_alpha
echo  * Web Dashboard: http://127.0.0.1:8080
echo  * Health Check:  http://127.0.0.1:8080/health
echo.
echo  [INFO] 24/7 Nazoratchi ishga tushirilmoqda...
echo.

python run_24_7.py

pause
