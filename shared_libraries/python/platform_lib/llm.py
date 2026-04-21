from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class RCAResult:
    summary: str
    confidence: float
    evidence: list[dict[str, Any]]
    provider: str


class HeuristicRCAProvider:
    def generate(self, incident: dict[str, Any], context: dict[str, Any]) -> RCAResult:
        summary_parts = []

        anomalies = context.get("anomalies") or []
        traces = context.get("traces") or []
        logs = context.get("logs") or []
        graph = context.get("service_graph") or []

        if anomalies:
            top = anomalies[0]
            summary_parts.append(
                f"Primary signal {top.get('type', 'anomaly')} on {top.get('service_name', 'unknown-service')} "
                f"crossed {top.get('severity', 'warning')} threshold."
            )
        if traces:
            summary_parts.append(f"{len(traces)} trace spans overlap incident window.")
        if graph:
            summary_parts.append(f"{len(graph)} service edge(s) involved in impacted call path.")
        if logs:
            summary_parts.append(f"{len(logs)} related log event(s) available for drill-down.")

        if not summary_parts:
            summary_parts.append("Insufficient correlated evidence. Investigate latest failing endpoint and recent rule breaches.")

        evidence = [
            {"kind": "anomaly", "count": len(anomalies)},
            {"kind": "trace", "count": len(traces)},
            {"kind": "log", "count": len(logs)},
            {"kind": "graph_edge", "count": len(graph)},
        ]

        return RCAResult(
            summary=" ".join(summary_parts),
            confidence=0.58 if anomalies or traces or logs else 0.25,
            evidence=evidence,
            provider="heuristic",
        )


class HostedLLMProvider:
    def __init__(self, endpoint: str, api_key: str | None, model: str) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model

    def generate(self, incident: dict[str, Any], context: dict[str, Any]) -> RCAResult:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "incident": incident,
            "context": context,
            "instruction": (
                "Return concise root cause analysis with likely cause, confidence 0-1, "
                "and evidence list. Suggestions must stay assistive."
            ),
        }
        response = httpx.post(self.endpoint, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        body = response.json()
        return RCAResult(
            summary=body.get("summary", "No RCA summary returned."),
            confidence=float(body.get("confidence", 0.5)),
            evidence=body.get("evidence", []),
            provider=body.get("provider", "hosted"),
        )
