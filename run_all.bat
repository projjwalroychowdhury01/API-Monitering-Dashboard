@echo off
setlocal

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR:~0,-1%
set DOCKER_PATH=%PROJECT_ROOT%\infrastructure\docker

echo ==============================
echo Starting Docker Infrastructure
echo ==============================

start cmd /k "cd /d "%DOCKER_PATH%" && docker-compose up"

echo Waiting for Kafka + ClickHouse + Redis + Postgres to be ready...
timeout /t 35 /nobreak > nul

echo ==============================
echo Starting API Gateway
echo ==============================
start cmd /k "cd /d "%PROJECT_ROOT%\services\api-gateway" && call "%PROJECT_ROOT%\venv\Scripts\activate" && uvicorn app.main:app --reload --port 8000"

echo ==============================
echo Starting Ingestion Service
echo ==============================
start cmd /k "cd /d "%PROJECT_ROOT%\services\ingestion-service" && call "%PROJECT_ROOT%\venv\Scripts\activate" && python -m uvicorn app.main:app --reload --port 8001"

echo ==============================
echo Starting Metrics API
echo ==============================
start cmd /k "cd /d "%PROJECT_ROOT%\services\metrics-api" && call "%PROJECT_ROOT%\venv\Scripts\activate" && uvicorn app.main:app --reload --port 8002"

echo ==============================
echo Starting Probe Workers
echo ==============================
start cmd /k "cd /d "%PROJECT_ROOT%\services\probe-workers" && call "%PROJECT_ROOT%\venv\Scripts\activate" && python -m app.main"

echo ==============================
echo Starting Aggregation Service
echo ==============================
start cmd /k "cd /d "%PROJECT_ROOT%\services\aggregation-service" && call "%PROJECT_ROOT%\venv\Scripts\activate" && python -m app.main"

echo ==============================
echo Starting Alert Engine
echo ==============================
start cmd /k "cd /d "%PROJECT_ROOT%\services\alert-engine" && call "%PROJECT_ROOT%\venv\Scripts\activate" && python -m app.main"

echo ==============================
echo Starting Anomaly Engine
echo ==============================
start cmd /k "cd /d "%PROJECT_ROOT%\services\anomaly-engine" && call "%PROJECT_ROOT%\venv\Scripts\activate" && uvicorn app.main:app --reload --port 8004"

echo ==============================
echo Starting WebSocket Service
echo ==============================
start cmd /k "cd /d "%PROJECT_ROOT%\services\websocket-service" && call "%PROJECT_ROOT%\venv\Scripts\activate" && uvicorn app.main:app --reload --port 8006"

echo ==============================
echo Starting RCA Service
echo ==============================
start cmd /k "cd /d "%PROJECT_ROOT%\services\rca-service" && call "%PROJECT_ROOT%\venv\Scripts\activate" && uvicorn app.main:app --reload --port 8007"

echo ==============================
echo Starting Dashboard
echo ==============================
start cmd /k "cd /d "%PROJECT_ROOT%\frontend\dashboard" && npm run dev"

echo ==============================
echo ALL SERVICES STARTED
echo ==============================

pause
