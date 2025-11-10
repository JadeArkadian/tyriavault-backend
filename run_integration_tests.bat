@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  TyriaVault - Integration Tests
echo ========================================
echo.

REM Colors for output (if possible)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "NC=[0m"

echo [1/6] Stopping previous containers...
docker compose -f docker-compose.test.yml down -v 2>nul

echo.
echo [2/6] Starting services (PostgreSQL and WireMock)...
docker compose -f docker-compose.test.yml up -d

if errorlevel 1 (
    echo %RED%Error starting services with Docker Compose%NC%
    exit /b 1
)

echo.
echo [3/6] Waiting for services to be ready...
timeout /t 5 /nobreak >nul

echo.
echo [4/6] Initializing database...
call app\tests\integration\setup_db.bat

if errorlevel 1 (
    echo %RED%Error initializing database%NC%
    docker compose -f docker-compose.test.yml down -v
    exit /b 1
)

echo.
echo [5/6] Starting application in background...
set ENV=test
start /B uvicorn app.main:api --host 0.0.0.0 --port 8000 --env-file .env.test

REM Wait a bit for the application to start
echo Waiting for application to start...
timeout /t 5 /nobreak >nul

echo.
echo [6/6] Running integration tests...
pytest app\tests\integration\ -v --tb=short

set TEST_RESULT=%errorlevel%

echo.
echo ========================================
echo  Cleanup
echo ========================================

echo Stopping services...
docker compose -f docker-compose.test.yml down -v

echo Stopping application...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)

echo.
if %TEST_RESULT% equ 0 (
    echo %GREEN%========================================%NC%
    echo %GREEN% TESTS COMPLETED SUCCESSFULLY%NC%
    echo %GREEN%========================================%NC%
) else (
    echo %RED%========================================%NC%
    echo %RED% TESTS FAILED%NC%
    echo %RED%========================================%NC%
)

exit /b %TEST_RESULT%

