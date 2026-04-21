"use client";

import { useEffect, useMemo, useState } from "react";

import { ConsoleShell } from "@/components/console-shell";
import { LatencyHistoryChart } from "@/components/latency-history-chart";
import { MetricCard } from "@/components/metric-card";
import { Panel } from "@/components/panel";
import { createEventsSocket, getAnomalies, getIncidents, getLatencyHistory, getLatencySnapshot, getServiceGraph, getTraces } from "@/lib/api";

type LiveEvent = {
  event_type: string;
  payload: Record<string, unknown>;
};

export default function OverviewPage() {
  const [endpointId] = useState("google-test");
  const [snapshot, setSnapshot] = useState({ p50: 0, p95: 0, p99: 0, request_count: 0, error_rate: 0 });
  const [history, setHistory] = useState<any[]>([]);
  const [traces, setTraces] = useState<any[]>([]);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [graph, setGraph] = useState<any[]>([]);
  const [events, setEvents] = useState<LiveEvent[]>([]);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      const [nextSnapshot, nextHistory, nextTraces, nextIncidents, nextAnomalies, nextGraph] = await Promise.all([
        getLatencySnapshot(endpointId),
        getLatencyHistory(endpointId),
        getTraces(),
        getIncidents(),
        getAnomalies(),
        getServiceGraph(),
      ]);
      if (!mounted) return;
      setSnapshot(nextSnapshot);
      setHistory(nextHistory);
      setTraces(nextTraces);
      setIncidents(nextIncidents);
      setAnomalies(nextAnomalies);
      setGraph(nextGraph);
    };

    load();
    const timer = window.setInterval(load, 15000);
    const socket = createEventsSocket();
    socket.onmessage = (message) => {
      const payload = JSON.parse(message.data) as LiveEvent;
      setEvents((previous) => [payload, ...previous].slice(0, 6));
    };

    return () => {
      mounted = false;
      window.clearInterval(timer);
      socket.close();
    };
  }, [endpointId]);

  const openIncidentCount = useMemo(
    () => incidents.filter((incident) => incident.status !== "resolved").length,
    [incidents],
  );

  return (
    <ConsoleShell title="Platform Overview" eyebrow="Query Plane">
      <section className="metric-grid">
        <MetricCard label="P95 Latency" value={`${snapshot.p95.toFixed(2)} ms`} helper="Latest 60-minute blended percentile" />
        <MetricCard label="Request Count" value={`${snapshot.request_count}`} helper="Synthetic + normalized telemetry rollups" />
        <MetricCard label="Error Rate" value={`${(snapshot.error_rate * 100).toFixed(2)}%`} helper="5xx and hard failures" />
        <MetricCard label="Open Incidents" value={`${openIncidentCount}`} helper="Live incident records in metadata store" />
      </section>

      <div className="content-grid">
        <Panel title="Latency History" description="Legacy probe route remains intact while new query-plane history sits beside it.">
          <LatencyHistoryChart data={history} />
        </Panel>

        <Panel title="Detection Radar" description="Rules-first anomalies produced from the latest metric windows.">
          <div className="stack-list">
            {anomalies.length ? (
              anomalies.slice(0, 5).map((anomaly) => (
                <article className="list-card" key={`${anomaly.type}-${anomaly.service_name}-${anomaly.endpoint_id}`}>
                  <div className="list-row">
                    <strong>{anomaly.service_name}</strong>
                    <span className={`pill ${anomaly.severity === "critical" ? "pill-danger" : "pill-live"}`}>
                      {anomaly.severity}
                    </span>
                  </div>
                  <p>{anomaly.message}</p>
                </article>
              ))
            ) : (
              <div className="empty-state">No active anomalies in the selected window.</div>
            )}
          </div>
        </Panel>
      </div>

      <div className="content-grid">
        <Panel title="Recent Traces" description="Distributed trace summaries from normalized telemetry.">
          <div className="table-shell">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Trace</th>
                  <th>Service</th>
                  <th>Endpoint</th>
                  <th>Avg Latency</th>
                </tr>
              </thead>
              <tbody>
                {traces.slice(0, 6).map((trace) => (
                  <tr key={trace.trace_id}>
                    <td>{trace.trace_id.slice(0, 10)}…</td>
                    <td>{trace.service_name}</td>
                    <td>{trace.endpoint_id || "n/a"}</td>
                    <td>{trace.avg_latency_ms.toFixed(2)} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Service Graph Edges" description="Derived upstream/downstream call relationships.">
          <div className="stack-list">
            {graph.length ? (
              graph.slice(0, 6).map((edge) => (
                <article className="list-card" key={`${edge.source_service}-${edge.target_service}`}>
                  <div className="list-row">
                    <strong>
                      {edge.source_service} → {edge.target_service}
                    </strong>
                    <span className="pill">{edge.edge_count} edges</span>
                  </div>
                  <p>{edge.endpoint_id || "cross-service flow"} · last seen {new Date(edge.last_seen_at).toLocaleString()}</p>
                </article>
              ))
            ) : (
              <div className="empty-state">Graph edges will appear once trace spans land in ClickHouse.</div>
            )}
          </div>
        </Panel>
      </div>

      <Panel title="Live Event Feed" description="Redis-backed websocket updates from alert and incident activity.">
        <div className="stack-list">
          {events.length ? (
            events.map((event, index) => (
              <article className="list-card" key={`${event.event_type}-${index}`}>
                <div className="list-row">
                  <strong>{event.event_type}</strong>
                  <span className="pill pill-live">{String(event.payload.severity ?? "info")}</span>
                </div>
                <p>{String(event.payload.message ?? "Realtime platform event")}</p>
              </article>
            ))
          ) : (
            <div className="empty-state">Alert and incident activity will stream here when the worker emits updates.</div>
          )}
        </div>
      </Panel>
    </ConsoleShell>
  );
}
