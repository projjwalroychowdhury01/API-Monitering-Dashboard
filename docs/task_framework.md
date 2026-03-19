# Antigravity Task Framework

This framework prevents AI from producing broken code or losing project direction.

---

# Step 1 — Identify Subsystem

Before coding, AI must identify the subsystem:

Example:

Subsystem: Probe Workers

Responsibilities:
- simulate API requests
- measure latency
- collect metrics

---

# Step 2 — Confirm Architecture Fit

AI must verify the subsystem belongs to the architecture.

Example pipeline:

Probe → Ingestion → Kafka → Aggregation → Storage → Query

---

# Step 3 — Define Components

Example for probe system:

components:

scheduler
http_probe
metrics_collector

---

# Step 4 — Define Interfaces

Each component must define:

inputs  
outputs  

Example:

http_probe

input:
endpoint URL

output:
latency metrics

---

# Step 5 — Define Data Schema

All telemetry must follow schema:
endpoint_id
timestamp
latency
status_code
region

---

# Step 6 — Implement

AI generates code only after:

architecture  
interfaces  
schema  

are defined.

---

# Step 7 — Validate

AI must verify:

• code compiles  
• dependencies valid  
• architecture preserved