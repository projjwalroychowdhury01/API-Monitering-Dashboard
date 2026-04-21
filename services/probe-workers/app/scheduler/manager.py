import asyncio
from typing import Any, Dict, List, Optional, cast
from asyncio import Task

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from ..http_probe.client import HttpProbe
from ..metrics.collector import MetricsCollector, ProbeResult
from ..config import settings
from ..logger import log
from datetime import datetime
import httpx

class ProbeScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.probe = HttpProbe()
        self.collector = MetricsCollector()
        self.interval = settings.PROBE_INTERVAL_SECONDS
        self.client = httpx.AsyncClient(timeout=5.0)
        self.semaphore = asyncio.Semaphore(20)  # limit concurrency

        # Configurable endpoints loaded from endpoints.json / env
        self.endpoints: List[Dict[str, str]] = self._validate_endpoints(settings.ENDPOINTS)
        self._task: Optional[Task] = None

    def _validate_endpoints(self, raw_endpoints: list) -> List[Dict[str, str]]:
        validated: List[Dict[str, str]] = []

        if not isinstance(raw_endpoints, list):
            log.warning("ENDPOINTS config is not a list. Falling back to default.")
            return validated

        for entry in raw_endpoints:
            if not isinstance(entry, dict):
                log.warning("Skipping invalid endpoint entry (not a dict): %s", str(entry))
                continue
            endpoint_id = entry.get("id")
            url = entry.get("url")
            if not endpoint_id or not url:
                log.warning("Skipping invalid endpoint entry (missing id/url): %s", str(entry))
                continue
            validated.append({"id": str(endpoint_id), "url": str(url)})

        if not validated:
            log.warning("No valid endpoints configured. Scheduler will have nothing to probe.")

        return validated

    async def execute_probe_task(self, endpoint_id: str, url: str):
        log.info(f"Executing probe for {endpoint_id} -> {url}")
        result = await self.probe.run_probe(endpoint_id, url)
        # Currently, we just log the structured telemetry
        log.info(f"Probe Result for {endpoint_id}: status={result.status_code}, latency={result.latency:.4f}s")
        # In a real-world scenario, we'd send this to the Ingestion Gateway here.

    async def _send_telemetry(self, telemetry):
        data = telemetry.model_dump()
        data["timestamp"] = int(data["timestamp"].timestamp())
        payload = [data]
        headers = {}
        if settings.INGEST_API_KEY:
            headers["X-API-Key"] = settings.INGEST_API_KEY

        async with self.semaphore:   # 🔥 control concurrency
            try:
                resp = await self.client.post(settings.INGEST_URL, json=payload, headers=headers)
                
                if resp.status_code >= 400:
                    log.debug(f"Telemetry POST returned status {resp.status_code}")

            except Exception as e:
                log.debug("Telemetry POST failed (silent)")
                print("HTTP ERROR:", str(e))

    async def close(self):
        await self.client.aclose()

    def start(self):
        # Schedule probe jobs for all configured endpoints
        for ep in self.endpoints:
            self.scheduler.add_job(
                self.execute_probe_task,
                'interval',
                seconds=settings.PROBE_INTERVAL_SECONDS,
                args=[ep["id"], ep["url"]],
                id=f"probe-{ep['id']}",
            )

        self.scheduler.start()
        cast(Any, log).info(
            "Scheduler started",
            extra={
                "interval_s": settings.PROBE_INTERVAL_SECONDS,
                "endpoints": [ep["id"] for ep in self.endpoints],
            },
        )

    async def run_scheduler(self):
        """
        Main loop for the probe scheduler.
        Runs probes concurrently and sleeps for the configured interval.
        """
        log.info(f"Starting Probe Scheduler | Interval: {self.interval}s")

        while True:
            try:
                # Prepare concurrent probe tasks
                tasks = [
                    self.probe.run_probe(ep["id"], ep["url"])
                    for ep in self.endpoints
                ]

                # Execute all probes in parallel (non-blocking)
                results = await asyncio.gather(*tasks, return_exceptions=True)

                telemetry_tasks = []

                for result in results:
                    if isinstance(result, Exception):
                        log.error(f"Probe execution failed: {str(result)}")
                        continue
                    
                    probe_result = cast(ProbeResult, result)
                    telemetry = self.collector.collect(probe_result)

                    log.info(f"SENDING TELEMETRY: {telemetry.model_dump()}") 

                    telemetry_tasks.append(self._send_telemetry(telemetry))

                # 🔥 execute with control
                await asyncio.gather(*telemetry_tasks, return_exceptions=True)

            except Exception as e:
                log.error(f"Error in scheduler loop: {str(e)}")

            # Wait for next cycle
            await asyncio.sleep(self.interval)

    def shutdown(self):
        self.scheduler.shutdown()
        log.info("Scheduler shut down")
