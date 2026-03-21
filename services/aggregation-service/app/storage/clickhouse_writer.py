from typing import List, Dict, Any
from clickhouse_driver import Client
from app.config import settings, logger
import asyncio
from datetime import datetime

class ClickHouseWriter:
    def __init__(self):
        self.client = Client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_db,
            user=settings.clickhouse_user,
            password=settings.clickhouse_password
        )
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Ensure the aggregated metrics table exists."""
        query = """
        CREATE TABLE IF NOT EXISTS aggregated_metrics (
            endpoint_id String,
            window_start DateTime,
            total_requests UInt64,
            error_count UInt64,
            error_rate Float64,
            avg_latency Float64,
            min_latency Float64,
            max_latency Float64,
            p50_latency Float64,
            p90_latency Float64,
            p99_latency Float64,
            region String
        ) ENGINE = MergeTree()
        ORDER BY (endpoint_id, window_start)
        """
        try:
            self.client.execute(query)
            logger.info("Ensured 'aggregated_metrics' table exists.")
        except Exception as e:
            logger.error(f"Failed to create table in ClickHouse: {e}")
            raise

    async def write_batch(self, metrics: List[Dict[str, Any]]):
        """Write a batch of aggregated metrics to ClickHouse asynchronously."""
        if not metrics:
            return

        # Prepare data tuple-based format as expected by clickhouse_driver
        data = [
            (
                m['endpoint_id'],
                m['window_start'],
                m['total_requests'],
                m['error_count'],
                m['error_rate'],
                m['avg_latency'],
                m['min_latency'],
                m['max_latency'],
                m['p50_latency'],
                m['p90_latency'],
                m['p99_latency'],
                m['region']
            )
            for m in metrics
        ]

        # Use asyncio.to_thread to run blocking ClickHouse driver in background
        query = "INSERT INTO aggregated_metrics VALUES"
        try:
            await asyncio.to_thread(self.client.execute, query, data)
            logger.info(f"Successfully inserted {len(metrics)} aggregated records into ClickHouse.")
        except Exception as e:
            logger.error(f"Failed to insert batch to ClickHouse: {e}")
            raise
