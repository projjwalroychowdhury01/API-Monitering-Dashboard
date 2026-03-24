@echo off

set PROJECT_ROOT=C:\Users\Projjwal\OneDrive\Desktop\API Monitering Dashboard\API-Monitering-Dashboard

echo Starting Docker...
start cmd /k "cd /d "%PROJECT_ROOT%\infrastructure\docker" && docker-compose up"

echo Waiting for services to boot...
timeout /t 20

echo Creating ClickHouse table...

docker exec -i docker-clickhouse-1 clickhouse-client --query "CREATE TABLE IF NOT EXISTS metrics_1m (endpoint_id String, timestamp UInt32, p50 Float32, p95 Float32, p99 Float32, request_count UInt32, error_rate Float32) ENGINE = MergeTree() PARTITION BY toDate(timestamp) ORDER BY (endpoint_id, timestamp);"

echo Starting Ingestion Service...
start cmd /k "cd /d "%PROJECT_ROOT%\services\ingestion-service" && call "%PROJECT_ROOT%\venv\Scripts\activate" && python -m uvicorn app.main:app --reload"

timeout /t 20

echo Starting Probe Workers...
start cmd /k "cd /d "%PROJECT_ROOT%\services\probe-workers" && call "%PROJECT_ROOT%\venv\Scripts\activate" && python -m app.main"

timeout /t 20

echo Starting Aggregation Service...
start cmd /k "cd /d "%PROJECT_ROOT%\services\aggregation-service" && call "%PROJECT_ROOT%\venv\Scripts\activate" && python -m app.main"

echo All services started!
pause