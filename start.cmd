@echo off
setlocal
title StarkLLM Launcher
cd /d "%~dp0"

echo ============================================
echo          Starting StarkLLM
echo          Windows Research Beta
echo ============================================
echo.
echo  Requires: Docker Desktop + Ollama running
echo  Default model: qwen3.8:27b
echo.
echo  [1/4] Cleaning previous containers...
docker rm -f starkllm-backend starkllm-frontend >nul 2>&1
docker compose down --remove-orphans >nul 2>&1
echo.
echo  [2/4] Building and starting containers...
docker compose up --build -d
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [ERROR] Docker Compose failed.
    echo  Make sure Docker Desktop is running, then try again.
    echo.
    pause
    exit /b 1
)
echo.
echo  [3/4] Waiting for services to initialise...
timeout /t 4 >nul
echo.
echo  [4/4] Opening StarkLLM in your browser...
start http://localhost:5173
echo.
echo ============================================
echo  StarkLLM is running!
echo  Access: http://localhost:5173
echo ============================================
echo.
