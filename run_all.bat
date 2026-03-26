@echo off

set PROJECT_ROOT=C:\Users\Projjwal\OneDrive\Desktop\API Monitering Dashboard\API-Monitering-Dashboard
set DOCKER_PATH=%PROJECT_ROOT%\infrastructure\docker
set CLICKHOUSE_CONTAINER=docker-clickhouse-1

echo ==============================
echo Starting Docker Infrastructure
echo ==============================

start cmd /k "cd /d "%DOCKER_PATH%" && docker-compose up"

echo Waiting for Kafka + ClickHouse to be ready...
timeout /t 30

echo ==============================
echo Ensuring ClickHouse Table
echo ==============================

docker exec -i %CLICKHOUSE_CONTAINER% clickhouse-client --query "DROP TABLE IF EXISTS metrics_1m;"
docker exec -i %CLICKHOUSE_CONTAINER% clickhouse-client --query "CREATE TABLE IF NOT EXISTS metrics_1m (endpoint_id String, timestamp DateTime, p50 Float32, p95 Float32, p99 Float32, request_count UInt32, error_rate Float32) ENGINE = MergeTree() PARTITION BY toDate(timestamp) ORDER BY (endpoint_id, timestamp) TTL timestamp + INTERVAL 30 DAY;"

docker exec -i %CLICKHOUSE_CONTAINER% clickhouse-client --query "DROP TABLE IF EXISTS metrics_5m;"
docker exec -i %CLICKHOUSE_CONTAINER% clickhouse-client --query "CREATE TABLE IF NOT EXISTS metrics_5m (endpoint_id String, timestamp DateTime, p50 Float32, p95 Float32, p99 Float32, request_count UInt32, error_rate Float32) ENGINE = MergeTree() PARTITION BY toDate(timestamp) ORDER BY (endpoint_id, timestamp) TTL timestamp + INTERVAL 90 DAY;"

docker exec -i %CLICKHOUSE_CONTAINER% clickhouse-client --query "DROP VIEW IF EXISTS metrics_5m_mv;"
docker exec -i %CLICKHOUSE_CONTAINER% clickhouse-client --query "CREATE MATERIALIZED VIEW metrics_5m_mv TO metrics_5m AS SELECT endpoint_id, timestamp, quantile(0.5)(p50) AS p50, quantile(0.95)(p95) AS p95, quantile(0.99)(p99) AS p99, sum(request_count) AS request_count, avg(error_rate) AS error_rate FROM (SELECT endpoint_id, toStartOfFiveMinute(timestamp) AS timestamp, p50, p95, p99, request_count, error_rate FROM metrics_1m) GROUP BY endpoint_id, timestamp;"

echo ==============================
echo Starting Ingestion Service
echo ==============================

start cmd /k "cd /d "%PROJECT_ROOT%\services\ingestion-service" && call "%PROJECT_ROOT%\venv\Scripts\activate" && python -m uvicorn app.main:app --reload --port 8001"

timeout /t 30

echo ==============================
echo Starting Probe Workers
echo ==============================

start cmd /k "cd /d "%PROJECT_ROOT%\services\probe-workers" && call "%PROJECT_ROOT%\venv\Scripts\activate" && python -m app.main"

timeout /t 30

echo ==============================
echo Starting Aggregation Service
echo ==============================

start cmd /k "cd /d "%PROJECT_ROOT%\services\aggregation-service" && call "%PROJECT_ROOT%\venv\Scripts\activate" && python -m app.main"

echo ==============================
echo ALL SERVICES STARTED SUCCESSFULLY
echo ==============================

pause