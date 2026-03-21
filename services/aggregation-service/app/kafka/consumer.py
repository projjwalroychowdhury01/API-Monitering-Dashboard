import json
from kafka import KafkaConsumer
from app.config import settings, logger

def consume():
    """
    Consumes messages from the raw metrics Kafka topic continuously.
    Yields parsed JSON events to the processing layer.
    """
    consumer = KafkaConsumer(
        settings.kafka_topic_raw,
        bootstrap_servers=settings.kafka_broker_url,
        group_id=settings.kafka_group_id,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True
    )

    logger.info(f"Started consuming from Kafka topic: {settings.kafka_topic_raw}")
    
    for message in consumer:
        yield message.value
