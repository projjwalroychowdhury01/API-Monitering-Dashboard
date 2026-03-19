# Architecture Guardrails

These rules protect the system architecture from corruption.

---

# Guardrail 1 — Pipeline Integrity

The telemetry pipeline must always remain:

Probe → Ingestion → Kafka → Aggregation → Storage → Query → Visualization

No shortcuts allowed.

---

# Guardrail 2 — Message Bus Centralization

All telemetry events must pass through Kafka.

Kafka ensures:

• replayability  
• fault tolerance  
• decoupled services

---

# Guardrail 3 — Service Independence

Each microservice must run independently.

Services communicate via:

HTTP  
Kafka events  

---

# Guardrail 4 — Data Storage Isolation

Only aggregation services may write to ClickHouse.

Other services cannot.

---

# Guardrail 5 — Cache Isolation

Redis is used only for query caching.

Never store raw telemetry in Redis.

---

# Guardrail 6 — Query Layer Responsibility

The dashboard must never query ClickHouse directly.

Instead:

Dashboard → Metrics API → Redis → ClickHouse

---

# Guardrail 7 — Stateless Services

All services must be stateless except:

ClickHouse  
Redis  

---

# Guardrail 8 — Horizontal Scalability

Every service must support horizontal scaling.

Stateless workers enable scaling.

---

# Guardrail 9 — Observability

All services must emit logs and metrics.

---

# Guardrail 10 — Security

Every external endpoint must enforce:

JWT authentication  
rate limiting