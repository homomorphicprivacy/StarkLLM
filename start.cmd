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
echo  [3/4] Waiting for backend to be ready...
echo  (This can take 1-2 minutes on first run while the backend initialises)
echo.
set HEALTH_URL=http://localhost:8000/health
set MAX_TRIES=90
set TRY=0

:poll_loop
set /a TRY+=1
if %TRY% GTR %MAX_TRIES% (
    echo.
    echo  [WARNING] Backend did not respond within 90 seconds.
    echo  It may still be starting. Opening browser anyway...
    goto open_browser
)
curl.exe -sf --max-time 2 %HEALTH_URL% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo  Backend is ready! (attempt %TRY%)
    goto open_browser
)
echo  Waiting for backend... [%TRY%/%MAX_TRIES%]
timeout /t 1 /nobreak >nul
goto poll_loop

:open_browser
echo.
echo  [4/4] Opening StarkLLM in your browser...
start http://localhost:5173
echo.
echo ============================================
echo  StarkLLM is running!
echo  Access: http://localhost:5173
echo ============================================
echo.
