# Backend Monorepo - Services

This directory contains the core microservices of the API Observability Platform.

## Service Overview

| Service | Responsibility |
|---------|----------------|
| `api-gateway` | Entry point for all external requests. Handles authentication, routing, and rate limiting. |
| `ingestion-service` | Receives raw telemetry from probes. Validates data against `TelemetryEvent` schema and publishes to Kafka. |
| `probe-workers` | Periodic jobs that simulate API requests and measure latency, DNS, and TLS metrics. |
| `aggregation-service` | Consumes raw telemetry from Kafka. Computes statistical aggregates (p50, p95, p99) and writes to ClickHouse. |
| `metrics-api` | Serves metrics data to the dashboard. Integrates with ClickHouse for queries and Redis for caching. |
| `alert-engine` | Evaluates live telemetry against user-defined alerting rules. |
| `websocket-service` | Streams real-time updates to the frontend dashboard. |
| `anomaly-engine` | ML service for detecting abnormal behavior patterns in the telemetry stream. |

## Development Standard

All services should use:
- **FastAPI** for HTTP interfaces.
- **Shared Libraries** for logging and schemas (found in `shared-libraries/python/`).
- **Structured Logging** for consistency.
- **Health Checks** at `/health`.
