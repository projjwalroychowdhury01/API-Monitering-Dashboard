from datetime import datetime, timezone
from typing import Dict, List, Any
import asyncio
from collections import defaultdict
from app.aggregators.metrics_calculator import MetricsCalculator
from app.config import logger

class WindowManager:
    def __init__(self, window_size_seconds: int = 60):
        self.window_size_seconds = window_size_seconds
        
        # Buffer structure:
        # window_start_timestamp (int) -> endpoint_id -> region -> [list of raw events]
        self.windows: Dict[int, Dict[str, Dict[str, List[Dict[str, Any]]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
        self.current_watermark: int = 0
        self.lock = asyncio.Lock()

    def process_event(self, event: Dict[str, Any]):
        """Ingest a raw event into the corresponding time window buffer."""
        try:
            timestamp_str = event.get('timestamp')
            if not timestamp_str:
                return

            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            ts_seconds = int(dt.timestamp())
            
            # Floor down to the window_size_seconds exactly
            window_start_ts = ts_seconds - (ts_seconds % self.window_size_seconds)
            
            endpoint_id = event.get('endpoint_id', 'unknown')
            region = event.get('region', 'unknown')
            
            # Non-blocking append (safe enough in asyncio if single Kafka consumption loop)
            # However, we'll acquire a lock if called from multiple async contexts
            self.windows[window_start_ts][endpoint_id][region].append(event)
            
            # Update watermark (highest seen event timestamp)
            if ts_seconds > self.current_watermark:
                self.current_watermark = ts_seconds

        except Exception as e:
            logger.error(f"Error processing event in window manager: {e}")

    async def get_closed_windows(self) -> List[Dict[str, Any]]:
        """
        Check for windows that have "closed" based on the current watermark
        and a small grace period (e.g., 5 seconds).
        Returns the aggregated records and shifts closed windows out of memory.
        """
        grace_period = 5  # Allow 5s of late arrival
        cutoff_ts = self.current_watermark - self.window_size_seconds - grace_period
        
        closed_ts_keys = []
        aggregated_results = []

        async with self.lock:
            for window_ts in list(self.windows.keys()):
                if window_ts < cutoff_ts:
                    closed_ts_keys.append(window_ts)

            # Process closed windows
            for ts in closed_ts_keys:
                endpoints_dict = self.windows.pop(ts)
                window_start_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                
                for endpoint_id, regions_dict in endpoints_dict.items():
                    for region, records in regions_dict.items():
                        calc_metric = MetricsCalculator.calculate_window_metrics(
                            endpoint_id=endpoint_id,
                            window_start=window_start_dt,
                            region=region,
                            records=records
                        )
                        if calc_metric:
                            aggregated_results.append(calc_metric)

        return aggregated_results
