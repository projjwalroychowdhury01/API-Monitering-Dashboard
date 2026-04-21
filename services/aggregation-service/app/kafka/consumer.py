import json

from kafka import KafkaConsumer

from app.config import logger, settings


def consume():
    consumer = KafkaConsumer(
        settings.KAFKA_TOPIC_RAW_METRICS,
        settings.KAFKA_TOPIC_TELEMETRY,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_GROUP_ID,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )

    logger.info(
        "Started consuming from Kafka topics: %s",
        ", ".join([settings.KAFKA_TOPIC_RAW_METRICS, settings.KAFKA_TOPIC_TELEMETRY]),
    )

    for message in consumer:
        yield {"topic": message.topic, "value": message.value}
