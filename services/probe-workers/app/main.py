import os
import sys
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

# When running as a script (python app/main.py), ensure the top-level package is importable
if __name__ == "__main__" and __package__ is None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if root not in sys.path:
        sys.path.insert(0, root)

from .scheduler.manager import ProbeScheduler
from .config import settings
from .logger import log

# Initialize Probe Scheduler
probe_scheduler = ProbeScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the scheduler
    log.info(f"Starting {settings.SERVICE_NAME} in region {settings.REGION}")
    probe_scheduler.start() # This starts apscheduler
    # Start the continuous probing loop as a background task
    probe_scheduler._task = asyncio.create_task(probe_scheduler.run_scheduler())
    yield
    # Shutdown: Stop the scheduler and cancel the background task
    log.info("Stopping probe-workers scheduler...")
    if probe_scheduler._task:
        probe_scheduler._task.cancel()
        try:
            await probe_scheduler._task
        except asyncio.CancelledError:
            log.info("Probe scheduler background task cancelled.")
    probe_scheduler.shutdown()

app = FastAPI(
    title="Probe Workers Service",
    lifespan=lifespan
)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "probe-workers",
        "region": settings.REGION,
        "active_jobs": len(probe_scheduler.scheduler.get_jobs())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
