@echo off
title FutureWay - Link Publico Seguro (Cloudflare Tunnel)
color 0b
echo ========================================================
echo   FUTUREWAY - INICIANDO LINK PUBLICO SEGURO (HTTPS)
echo ========================================================
echo.
echo [INFO] Certifique-se de que o Django esteja rodando em outro terminal:
echo        python manage.py runserver
echo.
echo [INFO] Gerando link publico seguro com certificado SSL...
echo.
cloudflared.exe tunnel --url http://127.0.0.1:8000
pause
