import json

from kafka import KafkaProducer  # type: ignore

from app.config import settings


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),  # type: ignore
        api_version=(0, 10),
    )


def send_event(producer: KafkaProducer, topic: str, payload: dict) -> None:
    producer.send(topic, payload).get(timeout=10)
