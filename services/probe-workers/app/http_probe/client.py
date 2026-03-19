import httpx
import time
import socket
from datetime import datetime
from ..metrics.collector import ProbeResult, ProbeMetrics
from ..config import settings
from ..logger import log as _log
import logging

# Ensure log is properly typed as a Logger instance
log: logging.Logger = _log if isinstance(_log, logging.Logger) else logging.getLogger(__name__)


class HttpProbe:
    def __init__(self, region: str = settings.REGION):
        self.region = region

    async def run_probe(self, endpoint_id: str, url: str) -> ProbeResult:
        timestamp = datetime.utcnow()
        metrics = ProbeMetrics()

        start_total = time.perf_counter()

        try:
            timeout = httpx.Timeout(settings.PROBE_TIMEOUT_SECONDS, connect=settings.PROBE_TIMEOUT_SECONDS)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                start_request = time.perf_counter()
                response = await client.get(url)
                end_request = time.perf_counter()

                total_latency = end_request - start_total
                metrics.server_response = end_request - start_request
                metrics.total_latency = total_latency

                return ProbeResult(
                    endpoint_id=endpoint_id,
                    timestamp=timestamp,
                    status_code=response.status_code,
                    latency=total_latency,
                    region=self.region,
                    metrics=metrics
                )

        except (httpx.TimeoutException, httpx.RequestError, socket.gaierror) as e:
            err_type = type(e).__name__
            duration = time.perf_counter() - start_total
            log.error(
                f"Probe failed for {endpoint_id} ({url}) - {err_type}: {e}",
                extra={
                    "endpoint_id": endpoint_id,
                    "url": url,
                    "error_type": err_type,
                    "duration_s": duration,
                },
            )
            return ProbeResult(
                endpoint_id=endpoint_id,
                timestamp=timestamp,
                status_code=0,
                latency=duration,
                region=self.region,
                metrics=ProbeMetrics(total_latency=duration),
                error=str(e),
            )

        except Exception as e:  # pragma: no cover
            duration = time.perf_counter() - start_total
            log.error(
                f"Unexpected probe failure for {endpoint_id} ({url}): {e}",
                extra={
                    "endpoint_id": endpoint_id,
                    "url": url,
                    "duration_s": duration,
                },
            )
            return ProbeResult(
                endpoint_id=endpoint_id,
                timestamp=timestamp,
                status_code=0,
                latency=duration,
                region=self.region,
                metrics=ProbeMetrics(total_latency=duration),
                error=str(e),
            )
