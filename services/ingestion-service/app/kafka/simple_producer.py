from kafka import KafkaProducer # type: ignore
import json
from app.logger import logger # type: ignore
from typing import Dict, Any

producer = None


def _init_producer():
    global producer
    if producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers="localhost:9092",
                value_serializer=lambda v: json.dumps(v).encode("utf-8") # type: ignore
            )
            logger.info("Initialized Kafka producer", extra={"bootstrap": "localhost:9092"}) # type: ignore
        except Exception as e:
            logger.error("Unable to initialize Kafka producer", extra={"error": str(e)}) # type: ignore
            raise


def send_metric(metric: Dict[str, Any]):
    _init_producer()
    try:
        producer.send("metrics_raw", metric) # type: ignore
    except Exception as e:
        logger.error("Failed to send metric to Kafka", extra={"error": str(e)}) # type: ignore
        raise
