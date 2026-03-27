# API Monitoring Dashboard

A production-grade API observability platform that probes external endpoints, streams raw latency events through Kafka, aggregates them into 1-minute and 5-minute windows in ClickHouse, caches results in Redis, and renders live percentile charts in a Next.js dashboard.

---

## Architecture Overview

```
┌─────────────────┐      HTTP probes      ┌──────────────────┐
│  Probe Workers  │ ──────────────────▶   │ External Endpoints│
│  (scheduler)    │                        └──────────────────┘
└────────┬────────┘
         │ raw latency events
         ▼
┌─────────────────┐
│ Ingestion Service│  ◀──── HTTP POST from probes
│   (FastAPI 8001) │
└────────┬─────────┘
         │ Kafka topic: raw_metrics
         ▼
┌─────────────────────┐
│ Aggregation Service  │  consumes raw_metrics, windows → 1 min / 5 min
└────────┬────────────┘
         │ writes p50/p95/p99 + error_rate
         ▼
┌──────────────┐      ┌──────────────┐
│  ClickHouse  │      │    Redis      │
│  (port 9000) │      │  (port 6379)  │
└──────┬───────┘      └──────┬────────┘
       │                     │ cache (TTL 60 s)
       └──────────┬──────────┘
                  ▼
       ┌─────────────────────┐
       │   Metrics API        │
       │   (FastAPI 8002)     │
       │   GET /metrics/latency│
       └──────────┬───────────┘
                  │ JSON
                  ▼
       ┌─────────────────────┐
       │  Next.js Dashboard   │
       │   (port 3000)        │
       └─────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Infrastructure** | Docker Compose, Apache Kafka (Confluent 7.5), Zookeeper |
| **Storage** | ClickHouse (MergeTree, Materialized Views), Redis 7 |
| **Backend services** | Python 3.11, FastAPI, Uvicorn, clickhouse-driver |
| **Frontend** | Next.js 16, React 19, Recharts, Axios, TypeScript |
| **Observability** | Kafka UI (port 8080) |

---

## Repository Structure

```
API-Monitering-Dashboard/
│
├── infrastructure/
│   └── docker/
│       ├── docker-compose.yml          # Kafka, ClickHouse, Redis, Kafka-UI, API Gateway
│       └── clickhouse/
│           └── default.xml             # ClickHouse no-password config
│
├── services/
│   ├── ingestion-service/              # FastAPI — receives raw probe events → Kafka
│   ├── probe-workers/                  # Scheduler — probes endpoints, POSTs to ingestion
│   │   └── endpoints.json             # List of monitored endpoints
│   ├── aggregation-service/           # Kafka consumer — aggregates into ClickHouse
│   ├── metrics-api/                   # FastAPI 8002 — serves latency percentiles
│   │   └── app/
│   │       ├── main.py                # CORS, router wiring, /health
│   │       ├── routes/metrics.py      # GET /metrics/latency
│   │       ├── db/clickhouse_client.py
│   │       └── services/
│   │           ├── cache_service.py   # Redis read/write
│   │           └── query_service.py   # ClickHouse query logic
│   ├── alert-engine/
│   ├── anomaly-engine/
│   ├── api-gateway/
│   └── websocket-service/
│
├── frontend/
│   └── dashboard/                     # Next.js app
│       ├── app/
│       │   ├── page.js                # Main dashboard page
│       │   └── layout.js
│       ├── components/
│       │   └── LatencyChart.js        # Recharts latency chart component
│       └── lib/
│           └── api.js                 # Axios client + getLatency()
│
├── run_all.bat                        # One-click Windows startup script
└── .gitignore
```

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Docker Desktop | Latest | Must be running before `run_all.bat` |
| Python | 3.11+ | Used for all backend services |
| Node.js | 18+ | Used for the Next.js dashboard |
| npm | 9+ | Comes with Node.js |

---

## Quick Start (Windows)

### 1. Clone the repo

```powershell
git clone https://github.com/projjwalroychowdhury01/API-Monitering-Dashboard.git
cd "API-Monitering-Dashboard"
```

### 2. Create a virtual environment and install Python dependencies

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Install frontend dependencies

```powershell
cd frontend\dashboard
npm install
cd ..\..
```

### 4. Configure environment variables

Copy the example env files and fill in your values:

```powershell
copy services\ingestion-service\.env.example services\ingestion-service\.env
copy services\metrics-api\.env.example       services\metrics-api\.env
copy services\probe-workers\.env.example     services\probe-workers\.env
```

> **Never commit `.env` files.** They are excluded by `.gitignore`.

### 5. Start everything with one command

```powershell
.\run_all.bat
```

This script:
1. Starts Docker (Kafka + Zookeeper + ClickHouse + Redis + Kafka-UI)
2. Waits 30 s for infrastructure to be ready
3. Creates the `metrics_1m` and `metrics_5m` ClickHouse tables and the `metrics_5m_mv` materialized view
4. Starts the **Ingestion Service** on port `8001`
5. Starts the **Probe Workers**
6. Starts the **Aggregation Service**
7. Starts the **Metrics API** on port `8002`
8. Starts the **Next.js Dashboard** on port `3000`

---

## Service Endpoints

| Service | URL | Description |
|---|---|---|
| Next.js Dashboard | http://localhost:3000 | Live latency chart UI |
| Metrics API | http://localhost:8002 | REST API for querying metrics |
| Metrics API — health | http://localhost:8002/health | Health check |
| Metrics API — docs | http://localhost:8002/docs | Auto-generated OpenAPI docs |
| Ingestion Service | http://localhost:8001 | Receives raw probe events |
| Kafka UI | http://localhost:8080 | Inspect Kafka topics and messages |
| ClickHouse HTTP | http://localhost:8123 | ClickHouse HTTP interface |

---

## API Reference

### `GET /metrics/latency`

Returns latency percentiles for a monitored endpoint.

**Query parameters**

| Parameter | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `endpoint_id` | string | ✅ | — | Non-empty |
| `minutes` | integer | ❌ | `60` | 1 – 1440 |

**Example**

```
GET http://localhost:8002/metrics/latency?endpoint_id=google-test&minutes=60
```

**Response**

```json
{
  "status": "success",
  "data": {
    "p50": 45.2,
    "p95": 120.8,
    "p99": 210.4,
    "request_count": 360,
    "error_rate": 0.02
  }
}
```

**Error response**

```json
{
  "detail": "Internal server error"
}
```

---

## Database Schema

### `metrics_1m` — 1-minute aggregated metrics (TTL: 30 days)

```sql
CREATE TABLE metrics_1m (
    endpoint_id   String,
    timestamp     DateTime,
    p50           Float32,
    p95           Float32,
    p99           Float32,
    request_count UInt32,
    error_rate    Float32
)
ENGINE = MergeTree()
PARTITION BY toDate(timestamp)
ORDER BY (endpoint_id, timestamp)
TTL timestamp + INTERVAL 30 DAY;
```

### `metrics_5m` — 5-minute rollup (TTL: 90 days)

Populated automatically via the `metrics_5m_mv` Materialized View.

---

## Adding a New Endpoint to Monitor

Edit `services/probe-workers/endpoints.json`:

```json
{
  "endpoints": [
    { "id": "google-test",  "url": "https://google.com" },
    { "id": "my-api",       "url": "https://api.example.com/health" }
  ]
}
```

Restart the probe workers after saving.

---

## Environment Variables

### `services/metrics-api/.env`

| Variable | Default | Description |
|---|---|---|
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated list of allowed CORS origins |

### `services/ingestion-service/.env`

| Variable | Default | Description |
|---|---|---|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:29092` | Kafka broker address |
| `KAFKA_TOPIC` | `raw_metrics` | Topic name for raw probe events |

### `frontend/dashboard/.env.local` (optional)

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_METRICS_API_URL` | `http://localhost:8002` | Base URL for the Metrics API |

---

## Security

- CORS is enforced via an allowlist — never uses `*`
- All API inputs are validated with Pydantic / FastAPI query constraints
- `.env` files are mandatory and never committed
- Passwords are not required for local ClickHouse (dev-only config)
- Rate limiting should be configured before any production deployment

---

## Running Services Individually

If you prefer to start each service manually instead of using `run_all.bat`:

```powershell
# 1. Infrastructure
cd infrastructure\docker
docker-compose up

# 2. Ingestion Service (new terminal)
cd services\ingestion-service
..\..\..\venv\Scripts\activate
uvicorn app.main:app --reload --port 8001

# 3. Probe Workers (new terminal)
cd services\probe-workers
..\..\..\venv\Scripts\activate
python -m app.main

# 4. Aggregation Service (new terminal)
cd services\aggregation-service
..\..\..\venv\Scripts\activate
python -m app.main

# 5. Metrics API (new terminal)
cd services\metrics-api
..\..\..\venv\Scripts\activate
uvicorn app.main:app --reload --port 8002

# 6. Dashboard (new terminal)
cd frontend\dashboard
npm run dev
```

---

## License

[Apache 2.0](LICENSE)