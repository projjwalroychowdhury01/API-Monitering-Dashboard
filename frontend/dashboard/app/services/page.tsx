"use client";

import { useEffect, useState } from "react";

import { ConsoleShell } from "@/components/console-shell";
import { Panel } from "@/components/panel";
import { getLogs, getServiceGraph } from "@/lib/api";

export default function ServicesPage() {
  const [graph, setGraph] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);

  useEffect(() => {
    void Promise.all([getServiceGraph(), getLogs()]).then(([nextGraph, nextLogs]) => {
      setGraph(nextGraph);
      setLogs(nextLogs);
    });
  }, []);

  return (
    <ConsoleShell title="Services & Dependency Graph" eyebrow="Topology">
      <div className="content-grid">
        <Panel title="Service Graph" description="Edge summaries derived from trace relationships.">
          <div className="table-shell">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Target</th>
                  <th>Endpoint</th>
                  <th>Edges</th>
                  <th>Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {graph.map((edge) => (
                  <tr key={`${edge.source_service}-${edge.target_service}-${edge.endpoint_id}`}>
                    <td>{edge.source_service}</td>
                    <td>{edge.target_service}</td>
                    <td>{edge.endpoint_id || "n/a"}</td>
                    <td>{edge.edge_count}</td>
                    <td>{new Date(edge.last_seen_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Recent Logs" description="Recent normalized log events from the shared telemetry pipeline.">
          <div className="stack-list">
            {logs.map((log) => (
              <article className="list-card" key={`${log.trace_id}-${log.timestamp}`}>
                <div className="list-row">
                  <strong>{log.service_name}</strong>
                  <span className="pill">{log.severity}</span>
                </div>
                <p>{log.message}</p>
              </article>
            ))}
          </div>
        </Panel>
      </div>
    </ConsoleShell>
  );
}
