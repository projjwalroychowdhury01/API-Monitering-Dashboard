"use client";

import { useEffect, useState } from "react";

import { ConsoleShell } from "@/components/console-shell";
import { Panel } from "@/components/panel";
import { type TraceSummary, getTraces } from "@/lib/api";

export default function TracesPage() {
  const [traces, setTraces] = useState<TraceSummary[]>([]);

  useEffect(() => {
    void getTraces().then(setTraces);
  }, []);

  return (
    <ConsoleShell title="Distributed Traces" eyebrow="Trace Query">
      <Panel title="Trace Search Results" description="Latest trace rollups from the normalized ingest path.">
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>Trace ID</th>
                <th>Service</th>
                <th>Endpoint</th>
                <th>Started</th>
                <th>Avg Latency</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {traces.map((trace) => (
                <tr key={trace.trace_id}>
                  <td>{trace.trace_id}</td>
                  <td>{trace.service_name}</td>
                  <td>{trace.endpoint_id || "n/a"}</td>
                  <td>{new Date(trace.started_at).toLocaleString()}</td>
                  <td>{trace.avg_latency_ms.toFixed(2)} ms</td>
                  <td>{trace.status_code}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </ConsoleShell>
  );
}
