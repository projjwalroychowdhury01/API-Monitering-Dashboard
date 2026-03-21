import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import logger
from app.aggregators.window_manager import WindowManager
from app.storage.clickhouse_writer import ClickHouseWriter
from app.kafka.consumer import MetricsConsumer

class AggregationApp:
    def __init__(self):
        self.writer = ClickHouseWriter()
        self.window_manager = WindowManager()
        self.consumer = MetricsConsumer(
            window_manager=self.window_manager,
            clickhouse_writer=self.writer
        )

app_instance = AggregationApp()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Aggregation Service...")
    consumer_task = asyncio.create_task(app_instance.consumer.start())
    yield
    # Shutdown
    logger.info("Shutting down Aggregation Service...")
    await app_instance.consumer.stop()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Aggregation Service",
    description="Aggregates metrics from Kafka and flushes to ClickHouse",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint required by architecture rules."""
    return {"status": "ok", "service": "aggregation-service"}

# Provide entry point for running directly if needed
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)
