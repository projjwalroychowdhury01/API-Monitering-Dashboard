"use client";

import { useEffect, useState } from "react";

import { ConsoleShell } from "@/components/console-shell";
import { Panel } from "@/components/panel";
import { getIncidentTimeline, getIncidents, getRca } from "@/lib/api";

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [rca, setRca] = useState<any | null>(null);

  useEffect(() => {
    void getIncidents().then((data) => {
      setIncidents(data);
      if (data.length) {
        setSelectedIncidentId(data[0].id);
      }
    });
  }, []);

  useEffect(() => {
    if (!selectedIncidentId) return;
    void Promise.all([getIncidentTimeline(selectedIncidentId), getRca(selectedIncidentId)]).then(([nextTimeline, nextRca]) => {
      setTimeline(nextTimeline);
      setRca(nextRca);
    });
  }, [selectedIncidentId]);

  return (
    <ConsoleShell title="Incidents" eyebrow="Incident Timeline">
      <div className="content-grid">
        <Panel title="Open Incident Records" description="Metadata-store-backed incidents created by the alert engine.">
          <div className="stack-list">
            {incidents.length ? (
              incidents.map((incident) => (
                <button
                  key={incident.id}
                  className={`list-card list-card-button ${selectedIncidentId === incident.id ? "is-selected" : ""}`}
                  onClick={() => setSelectedIncidentId(incident.id)}
                >
                  <div className="list-row">
                    <strong>{incident.title}</strong>
                    <span className={`pill ${incident.severity === "critical" ? "pill-danger" : "pill-live"}`}>
                      {incident.severity}
                    </span>
                  </div>
                  <p>{incident.summary}</p>
                </button>
              ))
            ) : (
              <div className="empty-state">No incidents yet. Trigger an alert cycle and they will appear here.</div>
            )}
          </div>
        </Panel>

        <Panel title="Timeline + RCA" description="Incident events and assistive root-cause suggestions.">
          {selectedIncidentId ? (
            <div className="stack-list">
              {rca ? (
                <article className="highlight-card">
                  <p className="eyebrow">Assistive RCA</p>
                  <strong>{rca.summary}</strong>
                  <p className="muted-copy">Confidence {(rca.confidence * 100).toFixed(0)}% · provider {rca.provider}</p>
                </article>
              ) : null}

              {timeline.map((event) => (
                <article className="list-card" key={event.id}>
                  <div className="list-row">
                    <strong>{event.event_type}</strong>
                    <span className="pill">{new Date(event.created_at).toLocaleTimeString()}</span>
                  </div>
                  <p>{event.message}</p>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state">Select an incident to inspect timeline and RCA.</div>
          )}
        </Panel>
      </div>
    </ConsoleShell>
  );
}
