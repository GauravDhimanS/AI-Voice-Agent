@echo off
REM Create self-signed SSL certificate for local HTTPS

echo ========================================
echo   Creating Self-Signed SSL Certificate
echo ========================================
echo.

REM Check if OpenSSL is available
where openssl >nul 2>&1
if errorlevel 1 (
    echo ERROR: OpenSSL not found!
    echo.
    echo Please install OpenSSL:
    echo   1. Download from: https://slproweb.com/products/Win32OpenSSL.html
    echo   2. Install "Win64 OpenSSL v3.x.x Light"
    echo   3. Add to PATH: C:\Program Files\OpenSSL-Win64\bin
    echo.
    echo OR use Option 2 below (PowerShell method)
    pause
    exit /b 1
)

echo Generating self-signed certificate...
echo.

openssl req -x509 -newkey rsa:4096 -nodes ^
    -keyout key.pem ^
    -out cert.pem ^
    -days 365 ^
    -subj "/C=US/ST=State/L=City/O=VoiceAgent/CN=localhost"

if errorlevel 1 (
    echo.
    echo ERROR: Certificate generation failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Certificate Created Successfully!
echo ========================================
echo.
echo Files created:
echo   - key.pem  (private key)
echo   - cert.pem (certificate)
echo.
echo To start server with HTTPS:
echo   uvicorn server:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem
echo.
echo Then access via:
echo   https://192.168.1.42:8000/web/app.html
echo.
echo NOTE: Your browser will show a security warning.
echo       Click "Advanced" and "Proceed" (it's safe, it's your own cert).
echo.
pause
