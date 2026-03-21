import logging
from app.kafka.consumer import consume
from app.aggregators.window_manager import WindowManager
from app.aggregators.metrics_calculator import calculate_metrics
from app.storage.clickhouse_writer import insert_metrics

# Re-use logger configuration from the project but simple loop based logic
from app.config import logger

wm = WindowManager(window_size=60)

def run():
    logger.info("Starting Aggregation Service main loop...")
    for event in consume():
        wm.add_event(event)

        if wm.should_flush():
            data = wm.flush()
            logger.info(f"Flushing {len(data)} endpoints to ClickHouse")

            for endpoint, events in data.items():
                metrics = calculate_metrics(events)
                insert_metrics(endpoint, metrics)

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        logger.info("Service stopped gracefully.")
    except Exception as e:
        logger.error(f"Service interrupted by error: {e}")
