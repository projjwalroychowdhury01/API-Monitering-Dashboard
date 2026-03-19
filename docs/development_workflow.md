# Development Workflow

This project must be implemented in controlled phases.

---

# Phase 1 — Project Setup

Create monorepo structure.

Initialize:

- backend services
- frontend
- shared libraries
- infrastructure

---

# Phase 2 — Probe Workers

Implement distributed probes.

Features:

• async HTTP probing
• latency measurement
• telemetry generation

---

# Phase 3 — Ingestion Gateway

Create FastAPI ingestion service.

Responsibilities:

• authentication
• schema validation
• Kafka publishing

---

# Phase 4 — Kafka Pipeline

Deploy Kafka cluster.

Create topics:

metrics_raw  
metrics_errors  
metrics_cache  

---

# Phase 5 — Aggregation Workers

Workers consume telemetry events.

Compute:

p50  
p95  
p99  
error_rate  

---

# Phase 6 — ClickHouse Storage

Create metrics schema.

Implement:

- partitions
- indexing
- retention

---

# Phase 7 — Metrics Query API

Expose REST API.

Example endpoint:

/metrics/latency

---

# Phase 8 — Redis Cache

Cache frequent queries.

TTL: 30–60 seconds

---

# Phase 9 — WebSocket Streaming

Push real-time metrics to dashboard.

---

# Phase 10 — Dashboard

Next.js dashboard.

Charts:

• latency
• traffic
• error rate

---

# Phase 11 — Alert Engine

Evaluate metric thresholds.

Send notifications.

---

# Phase 12 — Anomaly Detection

ML-based anomaly detection.