@echo off

set PROJECT_ROOT=C:\Users\Projjwal\OneDrive\Desktop\API Monitering Dashboard\API-Monitering-Dashboard
set DOCKER_PATH=%PROJECT_ROOT%\infrastructure\docker
set CLICKHOUSE_CONTAINER=docker-clickhouse-1

echo ==============================
echo Starting Docker Infrastructure
echo ==============================

start cmd /k "cd /d "%DOCKER_PATH%" && docker-compose up"

echo Waiting for Kafka + ClickHouse to be ready...
timeout /t 25

echo ==============================
echo Ensuring ClickHouse Table
echo ==============================

docker exec -i %CLICKHOUSE_CONTAINER% clickhouse-client --query "CREATE TABLE IF NOT EXISTS metrics_1m (endpoint_id String, timestamp UInt32, p50 Float32, p95 Float32, p99 Float32, request_count UInt32, error_rate Float32) ENGINE = MergeTree() PARTITION BY toDate(timestamp) ORDER BY (endpoint_id, timestamp);"

echo ==============================
echo Starting Ingestion Service
echo ==============================

start cmd /k "cd /d "%PROJECT_ROOT%\services\ingestion-service" && call "%PROJECT_ROOT%\venv\Scripts\activate" && python -m uvicorn app.main:app --reload"

timeout /t 5

echo ==============================
echo Starting Probe Workers
echo ==============================

start cmd /k "cd /d "%PROJECT_ROOT%\services\probe-workers" && call "%PROJECT_ROOT%\venv\Scripts\activate" && python -m app.main"

timeout /t 5

echo ==============================
echo Starting Aggregation Service
echo ==============================

start cmd /k "cd /d "%PROJECT_ROOT%\services\aggregation-service" && call "%PROJECT_ROOT%\venv\Scripts\activate" && python -m app.main"

echo ==============================
echo ALL SERVICES STARTED SUCCESSFULLY
echo ==============================

pause