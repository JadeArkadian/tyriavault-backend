@echo off
setlocal enabledelayedexpansion

echo Waiting for PostgreSQL to be ready...

:wait_postgres
docker exec tyriavault-postgres-test pg_isready -U test_user -d tyriavault_test >nul 2>&1
if errorlevel 1 (
    echo PostgreSQL is not ready yet, waiting...
    timeout /t 2 /nobreak >nul
    goto wait_postgres
)

echo PostgreSQL is ready

echo Running SQL schema (TyriaVault_Model.sql)...
docker exec -i tyriavault-postgres-test psql -U test_user -d tyriavault_test < TyriaVault_Model.sql

if errorlevel 1 (
    echo Error running SQL schema
    exit /b 1
)

echo Database initialized successfully

