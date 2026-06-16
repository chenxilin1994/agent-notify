@echo off
REM Quick start script for Agent Notify Desktop App

echo === Starting Agent Notify ===
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js not found!
    echo Please install from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if npm is installed
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: npm not found!
    pause
    exit /b 1
)

echo Node.js found:
node -v
echo npm found:
npm -v
echo.

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
    echo.
)

REM Start Electron
echo Starting Electron app...
call npm start