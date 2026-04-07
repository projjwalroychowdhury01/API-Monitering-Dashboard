# config.py
# Runtime configuration for the Alert Engine.
# Every value can be overridden via an environment variable.
# No third-party libraries — stdlib os only.

import os

# ---------------------------------------------------------------------------
# Polling
# ---------------------------------------------------------------------------

# Seconds between each metrics poll cycle.
POLL_INTERVAL: int = int(os.getenv("POLL_INTERVAL", "60"))

# ---------------------------------------------------------------------------
# Alert deduplication
# ---------------------------------------------------------------------------

# Seconds to suppress a repeated alert for the same (endpoint, type) pair.
ALERT_COOLDOWN: int = int(os.getenv("ALERT_COOLDOWN", "300"))

# ---------------------------------------------------------------------------
# ClickHouse connection
# ---------------------------------------------------------------------------

CLICKHOUSE_HOST: str = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT: int = int(os.getenv("CLICKHOUSE_PORT", "9000"))
