import time
from collections import defaultdict
from typing import Any


class WindowManager:
    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.buffer: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
        self.start_time = time.time()

    def add_event(self, event: dict[str, Any]) -> None:
        key = (
            event.get("tenant_id", "demo-tenant"),
            event.get("environment", "development"),
            event.get("service_name", "probe-workers"),
            event.get("endpoint_id", "unknown-endpoint"),
            event.get("region", "unknown"),
        )
        self.buffer[key].append(event)

    def should_flush(self) -> bool:
        return time.time() - self.start_time >= self.window_size

    def flush(self) -> dict[tuple[str, str, str, str, str], list[dict[str, Any]]]:
        data = dict(self.buffer)
        self.buffer.clear()
        self.start_time = time.time()
        return data
