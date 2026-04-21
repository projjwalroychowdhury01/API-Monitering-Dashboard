"use client";

import { useEffect, useState } from "react";

import { ConsoleShell } from "@/components/console-shell";
import { Panel } from "@/components/panel";
import { createEventsSocket, getAnomalies, listAlertRules } from "@/lib/api";

export default function AlertsPage() {
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [rules, setRules] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    void Promise.all([getAnomalies(), listAlertRules()]).then(([nextAnomalies, nextRules]) => {
      setAnomalies(nextAnomalies);
      setRules(nextRules);
    });

    const socket = createEventsSocket();
    socket.onmessage = (message) => {
      setEvents((previous) => [JSON.parse(message.data), ...previous].slice(0, 8));
    };

    return () => socket.close();
  }, []);

  return (
    <ConsoleShell title="Alerts & Detection" eyebrow="Rule Engine">
      <div className="content-grid">
        <Panel title="Configured Alert Rules" description="Control-plane rules applied by the alert engine.">
          <div className="stack-list">
            {rules.length ? (
              rules.map((rule) => (
                <article className="list-card" key={rule.id}>
                  <div className="list-row">
                    <strong>{rule.name}</strong>
                    <span className="pill">{rule.severity}</span>
                  </div>
                  <p>
                    {rule.metric_name} {rule.operator} {rule.threshold} · cooldown {rule.cool_down_seconds}s
                  </p>
                </article>
              ))
            ) : (
              <div className="empty-state">No rules configured yet. Create one from Settings.</div>
            )}
          </div>
        </Panel>

        <Panel title="Active Anomalies" description="Rules-first anomaly candidates surfaced from recent metric windows.">
          <div className="stack-list">
            {anomalies.length ? (
              anomalies.map((anomaly) => (
                <article className="list-card" key={`${anomaly.service_name}-${anomaly.endpoint_id}-${anomaly.type}`}>
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
              <div className="empty-state">No anomaly candidates right now.</div>
            )}
          </div>
        </Panel>
      </div>

      <Panel title="Realtime Alert Feed" description="Websocket bridge from Redis-backed alert events.">
        <div className="stack-list">
          {events.length ? (
            events.map((event, index) => (
              <article className="list-card" key={`${event.event_type}-${index}`}>
                <div className="list-row">
                  <strong>{event.event_type}</strong>
                  <span className="pill">{String(event.payload.severity ?? "info")}</span>
                </div>
                <p>{String(event.payload.message ?? "No message")}</p>
              </article>
            ))
          ) : (
            <div className="empty-state">No live alerts received yet.</div>
          )}
        </div>
      </Panel>
    </ConsoleShell>
  );
}
