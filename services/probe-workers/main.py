import asyncio
from app.scheduler.scheduler import run_scheduler

if __name__ == "__main__":
    asyncio.run(run_scheduler())