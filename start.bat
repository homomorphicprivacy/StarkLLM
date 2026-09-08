@echo off
setlocal
title StarkLLM Control Panel
cd /d "%~dp0"

:menu
cls
echo ============================================
echo          StarkLLM Control Panel
echo          Windows Research Beta
echo ============================================
echo.
echo  1.  Start StarkLLM
echo  2.  Stop  StarkLLM
echo  3.  Exit
echo.
echo ============================================
echo  Requires: Docker Desktop + Ollama running
echo  Default model: qwen3.8:27b
echo ============================================
echo.
set "choice="
set /p choice="Enter choice [1/2/3]: "

if "%choice%"=="1" goto start_app
if "%choice%"=="2" goto stop_app
if "%choice%"=="3" goto exit_app

echo.
echo  Invalid choice. Please enter 1, 2, or 3.
timeout /t 2 >nul
goto menu

:start_app
cls
echo ============================================
echo         Starting StarkLLM
echo ============================================
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
    goto menu
)
echo.
echo  [2/3] Waiting for services to initialise...
timeout /t 4 >nul
echo.
echo  [3/3] Opening StarkLLM in your browser...
start http://localhost:5173
echo.
echo ============================================
echo  StarkLLM is running!
echo  Access: http://localhost:5173
echo ============================================
echo.
pause
goto menu

:stop_app
cls
echo ============================================
echo         Stopping StarkLLM
echo ============================================
echo.
docker compose down
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [ERROR] Failed to stop StarkLLM.
    echo.
    pause
    goto menu
)
echo.
echo ============================================
echo  StarkLLM stopped successfully.
echo ============================================
echo.
pause
goto menu

:exit_app
endlocal
exit /b 0
