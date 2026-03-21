from clickhouse_driver import Client
import time

client = Client(
    host="localhost",
    port=9000,
    user="default",
    password="",     # IMPORTANT
    secure=False
)

def insert_metrics(endpoint_id, metrics):
    """
    Inserts a single metric record.
    """
    client.execute(
        """
        INSERT INTO metrics_1m (
            endpoint_id,
            timestamp,
            p50,
            p95,
            p99,
            request_count,
            error_rate
        ) VALUES
        """,
        [(
            endpoint_id,
            int(time.time()),
            metrics["p50"],
            metrics["p95"],
            metrics["p99"],
            metrics["request_count"],
            metrics["error_rate"]
        )]
    )

def insert_metrics_batch(batch_data):
    """
    Batch insert support.
    batch_data should be a list of tuples: (endpoint_id, metrics_dict)
    """
    if not batch_data:
        return

    timestamp = int(time.time())
    
    values = [
        (
            endpoint_id,
            timestamp,
            metrics["p50"],
            metrics["p95"],
            metrics["p99"],
            metrics["request_count"],
            metrics["error_rate"]
        )
        for endpoint_id, metrics in batch_data
    ]

    client.execute(
        """
        INSERT INTO metrics_1m (
            endpoint_id,
            timestamp,
            p50,
            p95,
            p99,
            request_count,
            error_rate
        ) VALUES
        """,
        values
    )
