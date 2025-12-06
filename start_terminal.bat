@echo off
REM Quick start script for the Voice Agent Terminal Mode

echo ========================================
echo   AI Voice Agent - Terminal Mode
echo ========================================
echo.

REM Check if Ollama is running
echo [1/2] Checking Ollama server...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ERROR: Ollama is not running!
    echo Please start Ollama first: ollama serve
    echo.
    pause
    exit /b 1
)
echo     OK - Ollama is running

REM Start in text mode (faster for testing)
echo.
echo [2/2] Starting voice agent in TEXT mode...
echo.
echo ========================================
echo   Text Mode (no voice input/output)
echo   For voice mode, run: python main.py
echo ========================================
echo.

call voice_agent\Scripts\python.exe main.py --text
