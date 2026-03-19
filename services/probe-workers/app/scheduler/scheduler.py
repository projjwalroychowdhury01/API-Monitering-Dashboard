"""
Probe Scheduler Module

Provides a clean interface for running the probe scheduler.
"""

import asyncio  # type: ignore
from .manager import ProbeScheduler
from ..logger import log  # type: ignore


async def run_scheduler():
    """
    Main entry point for running the probe scheduler.

    This function initializes the probe scheduler and runs the main probe loop.
    It handles proper async event loop management and clean startup/shutdown.
    """
    log.info("Starting Probe Workers Service")  # type: ignore

    scheduler = ProbeScheduler()

    try:
        # Run the main scheduler loop
        await scheduler.run_scheduler()
    except KeyboardInterrupt:
        log.info("Received shutdown signal")  # type: ignore
    except Exception as e:
        log.error(f"Fatal error in scheduler: {e}")  # type: ignore
        raise
    finally:
        # Clean shutdown
        scheduler.shutdown()
        log.info("Probe Workers Service stopped")  # type: ignore