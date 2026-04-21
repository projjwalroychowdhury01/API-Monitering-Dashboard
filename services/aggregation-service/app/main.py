import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared_libraries/python")))

from platform_lib.telemetry import TelemetryEnvelope

from app.aggregators.metrics_calculator import calculate_metrics
from app.aggregators.window_manager import WindowManager
from app.config import logger, settings
from app.kafka.consumer import consume
from app.storage.clickhouse_writer import (
    ensure_tables,
    insert_log_event,
    insert_metrics_rollup,
    insert_service_graph_edge,
    insert_trace_span,
)


wm = WindowManager(window_size=settings.AGGREGATION_WINDOW_SECONDS)


def run():
    ensure_tables()
    logger.info("Starting Aggregation Service main loop...")
    for message in consume():
        topic = message["topic"]
        payload = message["value"]

        if topic == settings.KAFKA_TOPIC_RAW_METRICS:
            wm.add_event(
                {
                    "tenant_id": "demo-tenant",
                    "environment": "development",
                    "service_name": "probe-workers",
                    "endpoint_id": payload["endpoint_id"],
                    "region": payload.get("region", "local"),
                    "latency_ms": float(payload.get("latency", 0.0)),
                    "status_code": payload.get("status_code", 0),
                }
            )
        else:
            event = TelemetryEnvelope.model_validate(payload)
            event_payload = event.model_dump(mode="json")

            if event.signal_type == "metric" and event.endpoint_id:
                wm.add_event(event_payload)
            elif event.signal_type == "trace":
                insert_trace_span(event_payload)
                insert_service_graph_edge(event_payload)
            elif event.signal_type == "log":
                insert_log_event(event_payload)

        if wm.should_flush():
            data = wm.flush()
            logger.info("Flushing %s metric groups to ClickHouse", len(data))
            for key, events in data.items():
                insert_metrics_rollup(key, calculate_metrics(events))


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        logger.info("Service stopped gracefully.")
    except Exception as exc:
        logger.error("Service interrupted by error: %s", exc)
