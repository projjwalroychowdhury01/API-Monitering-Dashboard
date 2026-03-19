# Global Development Rules

These rules govern all AI-assisted development for the API Observability Platform.

The system architecture defined in `Project_architecture.md` is the single source of truth.

AI must follow these rules strictly.

---

# 1. Architecture First Rule

AI must never invent architecture.

All implementations must follow the architecture layers:

Probe → Ingestion → Streaming → Aggregation → Storage → Query → Visualization

---

# 2. No Skipping Layers

AI must never skip pipeline stages.

Example:

Probe → Kafka → ClickHouse → Dashboard

This is invalid.

Correct pipeline:

Probe → Ingestion Gateway → Kafka → Aggregation → ClickHouse → Query API → Dashboard

---

# 3. Microservice Boundary Rule

Each service must remain independent.

Allowed services:

- api-gateway
- ingestion-service
- probe-workers
- aggregation-service
- metrics-api
- alert-engine
- websocket-service
- anomaly-engine

AI must not merge services.

---

# 4. Incremental Development Rule

AI must never generate the entire project at once.

Implementation must occur in small phases.

Each phase must:

1. Implement one subsystem
2. Compile successfully
3. Be testable

---

# 5. Deterministic Code Rule

All generated code must:

- compile
- run
- have no placeholders
- have no pseudo-code

Forbidden:

TODO
FIXME
"implement later"

---

# 6. Dependency Discipline

Only use required libraries.

Approved stack:

Backend:
- FastAPI
- asyncio
- httpx
- kafka-python
- redis
- clickhouse-driver

Frontend:
- Next.js
- WebSockets

Infrastructure:
- Docker
- Kubernetes

---

# 7. Event Driven Rule

All telemetry must pass through the streaming system.

Kafka is the central message bus.

Direct writes to ClickHouse from probes are forbidden.

---

# 8. Time Series Rule

Metrics must always contain:

timestamp  
endpoint_id  
latency  
status_code  
region  

---

# 9. No Hidden State

All services must be stateless except:

ClickHouse  
Redis  

---

# 10. Testing Rule

Every service must include:

- health endpoint
- logging
- minimal integration test