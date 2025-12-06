@echo off
REM Quick start script for the Voice Agent Web UI

echo ========================================
echo   AI Voice Agent - Web UI Launcher
echo ========================================
echo.

REM Check if Ollama is running
echo [1/3] Checking Ollama server...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ERROR: Ollama is not running!
    echo Please start Ollama first: ollama serve
    echo.
    pause
    exit /b 1
)
echo     OK - Ollama is running

REM Run diagnostics
echo.
echo [2/3] Running diagnostics...
call voice_agent\Scripts\python.exe test_setup.py
if errorlevel 1 (
    echo.
    echo ERROR: Diagnostics failed. Please fix the issues above.
    pause
    exit /b 1
)

REM Start the server
echo.
echo [3/3] Starting web server...
echo.
echo ========================================
echo   Server starting on http://localhost:8000
echo   Open in browser: http://localhost:8000/web/
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

call voice_agent\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000
