from kafka import KafkaProducer #type: ignore
import json
from typing import Dict, Any

producer = None

def init_producer():
    global producer
    producer = KafkaProducer(
        bootstrap_servers="localhost:29092",
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),  #type: ignore
        api_version=(0, 10)
    )

def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers="localhost:29092",
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),#type: ignore
        api_version=(0, 10)
    )

def get_producer():
    return producer

def send_metric(metric: Dict[str, Any]) -> None:
    if producer is None:
        init_producer()
    producer.send("metrics_raw", metric) # type: ignore
    producer.flush() # type: ignore