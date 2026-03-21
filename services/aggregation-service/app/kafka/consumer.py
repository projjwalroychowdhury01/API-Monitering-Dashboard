import asyncio
import json
from aiokafka import AIOKafkaConsumer
from app.config import settings, logger
from app.aggregators.window_manager import WindowManager
from app.storage.clickhouse_writer import ClickHouseWriter

class MetricsConsumer:
    def __init__(self, window_manager: WindowManager, clickhouse_writer: ClickHouseWriter):
        self.window_manager = window_manager
        self.clickhouse_writer = clickhouse_writer
        self.consumer = None
        self._running = False

    async def start(self):
        """Start the Kafka consumer loop."""
        self.consumer = AIOKafkaConsumer(
            settings.kafka_topic_raw,
            bootstrap_servers=settings.kafka_broker_url,
            group_id=settings.kafka_group_id,
            auto_offset_reset='latest'
        )
        await self.consumer.start()
        self._running = True
        logger.info(f"Started consuming from Kafka topic: {settings.kafka_topic_raw}")

        # Start background task for flushing windows
        asyncio.create_task(self._window_flusher())

        try:
            async for msg in self.consumer:
                if not self._running:
                    break
                try:
                    event = json.loads(msg.value.decode('utf-8'))
                    await self.window_manager.process_event(event)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON received from Kafka")
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {e}")
        finally:
            await self.stop()

    async def _window_flusher(self):
        """Periodically check and flush closed windows to ClickHouse."""
        while self._running:
            try:
                closed_windows = await self.window_manager.get_closed_windows()
                if closed_windows:
                    logger.info(f"Flushing {len(closed_windows)} closed windows to ClickHouse")
                    await self.clickhouse_writer.write_batch(closed_windows)
            except Exception as e:
                logger.error(f"Error flushing windows: {e}")
            
            await asyncio.sleep(5)  # Check every 5 seconds

    async def stop(self):
        """Stop the consumer and cleanup."""
        self._running = False
        if self.consumer:
            await self.consumer.stop()
        logger.info("Kafka consumer stopped")
