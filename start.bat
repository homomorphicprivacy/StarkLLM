@echo off
title StarkLLM Control Panel
cls

:menu
cls
echo ====================================
echo        StarkLLM Control Panel
echo ====================================
echo 1. Start StarkLLM
echo 2. Stop StarkLLM
echo 3. Exit
echo ====================================
set /p choice="Enter your choice (1/2/3): "

if "%choice%"=="1" goto start_app
if "%choice%"=="2" goto stop_app
if "%choice%"=="3" goto exit_app

echo.
echo Invalid choice. Please select 1, 2, or 3.
timeout /t 2 >nul
goto menu

:start_app
cls
echo ====================================
echo          Starting StarkLLM
echo ====================================
echo.
echo [1/3] Navigating to project directory...
cd /d "%~dp0"

echo.
echo [2/3] Building and starting StarkLLM Docker containers...
docker compose up --build -d
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Docker Compose failed to start.
    echo Please make sure Docker Desktop is running and try again.
    echo.
    pause
    goto menu
)

echo.
echo [3/3] Opening StarkLLM in your browser...
start http://localhost:5173

echo.
echo ====================================
echo StarkLLM is running!
echo Access URL: http://localhost:5173
echo ====================================
echo.
pause
goto menu

:stop_app
cls
echo ====================================
echo          Stopping StarkLLM
echo ====================================
echo.
echo [1/2] Navigating to project directory...
cd /d "%~dp0"

echo.
echo [2/2] Stopping StarkLLM Docker containers...
docker compose down
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to stop StarkLLM.
    echo.
    pause
    goto menu
)

echo.
echo ====================================
echo StarkLLM has been successfully stopped.
echo ====================================
echo.
pause
goto menu

:exit_app
exit
