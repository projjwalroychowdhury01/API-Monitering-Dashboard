"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { getLatency } from "../lib/api";
import LatencyChart from "../components/LatencyChart";

// ─── Tokens (mirror globals.css vars for inline styles) ──────────────────────

const T = {
  surface: "rgba(255,255,255,0.04)",
  surfaceHv: "rgba(255,255,255,0.07)",
  border: "rgba(255,255,255,0.08)",
  borderHv: "rgba(255,255,255,0.16)",
  muted: "#64748b",
  faint: "#334155",
};

// ─── MetricCard ───────────────────────────────────────────────────────────────

/**
 * A single statistic card.
 * @param {{ label: string, value: string|null, unit: string, accent: string, note: string }} props
 */
function MetricCard({ label, value, unit = "ms", accent = "#6366f1", note }) {
  return (
    <article
      style={{
        position: "relative",
        overflow: "hidden",
        background: T.surface,
        border: `1px solid ${T.border}`,
        borderRadius: "var(--radius-card)",
        padding: "1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
        transition: "border-color 0.2s, background 0.2s",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = T.surfaceHv;
        e.currentTarget.style.borderColor = T.borderHv;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = T.surface;
        e.currentTarget.style.borderColor = T.border;
      }}
    >
      {/* Accent glow */}
      <span
        aria-hidden
        style={{
          position: "absolute",
          top: "-2rem",
          right: "-2rem",
          width: "6rem",
          height: "6rem",
          borderRadius: "9999px",
          background: accent,
          opacity: 0.15,
          filter: "blur(32px)",
          pointerEvents: "none",
        }}
      />

      {/* Label */}
      <span
        style={{
          fontSize: "0.7rem",
          fontWeight: 600,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          color: T.muted,
        }}
      >
        {label}
      </span>

      {/* Value */}
      <div style={{ display: "flex", alignItems: "baseline", gap: "0.25rem" }}>
        <span
          style={{
            fontSize: "2.5rem",
            fontWeight: 700,
            letterSpacing: "-0.03em",
            color: "#f1f5f9",
            fontVariantNumeric: "tabular-nums",
            lineHeight: 1,
          }}
        >
          {value ?? "—"}
        </span>
        {unit && (
          <span style={{ fontSize: "0.85rem", color: T.muted, fontWeight: 500 }}>
            {unit}
          </span>
        )}
      </div>

      {/* Note */}
      {note && (
        <span style={{ fontSize: "0.75rem", color: T.faint }}>{note}</span>
      )}
    </article>
  );
}

// ─── SectionHeading ───────────────────────────────────────────────────────────

function SectionHeading({ children }) {
  return (
    <h2
      style={{
        fontSize: "0.7rem",
        fontWeight: 600,
        letterSpacing: "0.12em",
        textTransform: "uppercase",
        color: T.muted,
        marginBottom: "0.75rem",
      }}
    >
      {children}
    </h2>
  );
}

// ─── StatusBadge ─────────────────────────────────────────────────────────────

function StatusBadge({ loading, error, lastUpdated }) {
  const base = {
    display: "inline-flex",
    alignItems: "center",
    gap: "0.4rem",
    padding: "0.25rem 0.75rem",
    borderRadius: "9999px",
    fontSize: "0.75rem",
    fontWeight: 500,
  };
  const dot = {
    width: "0.45rem",
    height: "0.45rem",
    borderRadius: "9999px",
    flexShrink: 0,
  };

  if (error)
    return (
      <span style={{ ...base, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)", color: "#f87171" }}>
        <span style={{ ...dot, background: "#f87171" }} /> Error
      </span>
    );

  if (loading)
    return (
      <span style={{ ...base, background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.25)", color: "#818cf8" }}>
        <span style={{ ...dot, background: "#818cf8", animation: "pulse 1.5s ease-in-out infinite" }} /> Fetching…
      </span>
    );

  if (lastUpdated)
    return (
      <span style={{ ...base, background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.25)", color: "#34d399" }}>
        <span style={{ ...dot, background: "#34d399" }} /> Live · {lastUpdated}
      </span>
    );

  return null;
}

// ─── DashboardPage ────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [endpointId, setEndpointId] = useState("google-test");
  const [inputValue, setInputValue] = useState("google-test");
  const [minutes, setMinutes] = useState(60);
  const [metrics, setMetrics] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const intervalRef = useRef(null);
  const isFetchingRef = useRef(false);
  const abortCtrlRef = useRef(null);

  const MAX_HISTORY = 30;

  // ── Fetch ────────────────────────────────────────────────────────────────

  const fetchMetrics = useCallback(async (signal) => {
    if (!endpointId) return;
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;

    setLoading(true);
    setError(null);
    try {
      const data = await getLatency(endpointId, minutes, signal);
      if (signal?.aborted) return;

      setMetrics(data);
      const timestamp = new Date().toLocaleTimeString();
      setLastUpdated(timestamp);

      setHistory((prev) => {
        const point = { time: timestamp, p50: data.p50, p95: data.p95, p99: data.p99 };
        const next = [...prev, point];
        return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next;
      });
    } catch (err) {
      if (err.name !== "CanceledError" && err.name !== "AbortError") {
        setError(err.message);
      }
    } finally {
      if (!signal?.aborted) setLoading(false);
      isFetchingRef.current = false;
    }
  }, [endpointId, minutes]);

  // ── Polling ──────────────────────────────────────────────────────────────

  useEffect(() => {
    const ctrl = new AbortController();
    abortCtrlRef.current = ctrl;

    fetchMetrics(ctrl.signal);
    intervalRef.current = setInterval(() => fetchMetrics(ctrl.signal), 1000);

    return () => {
      ctrl.abort();
      clearInterval(intervalRef.current);
      isFetchingRef.current = false;
    };
  }, [fetchMetrics]);

  // ── Helpers ──────────────────────────────────────────────────────────────

  const handleApply = (e) => {
    e.preventDefault();
    setHistory([]);
    setEndpointId(inputValue.trim());
  };

  const fmt = (n, d = 2) => (n != null ? Number(n).toFixed(d) : null);

  const windowLabel = minutes >= 60 ? `${minutes / 60}h` : `${minutes}m`;

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <>
      {/* Keyframe for loading dot pulse */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.35; }
        }
      `}</style>

      {/* Ambient background glows */}
      <div aria-hidden style={{ position: "fixed", inset: 0, zIndex: -1, overflow: "hidden", pointerEvents: "none" }}>
        <div style={{ position: "absolute", top: "-10rem", left: "50%", transform: "translateX(-50%)", width: "45rem", height: "45rem", borderRadius: "9999px", background: "radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)" }} />
        <div style={{ position: "absolute", bottom: 0, right: 0, width: "28rem", height: "28rem", borderRadius: "9999px", background: "radial-gradient(circle, rgba(6,182,212,0.06) 0%, transparent 70%)" }} />
      </div>

      <main style={{ minHeight: "100vh", padding: "3rem 1.25rem 5rem" }}>

        {/* ── Centered container ── */}
        <div style={{ maxWidth: "56rem", margin: "0 auto", display: "flex", flexDirection: "column", gap: "2.5rem" }}>

          {/* ── Header ── */}
          <header>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.4rem" }}>
              <span style={{ width: "0.25rem", height: "2rem", borderRadius: "9999px", background: "linear-gradient(180deg, #818cf8, #22d3ee)", flexShrink: 0 }} />
              <h1 style={{ fontSize: "clamp(1.5rem, 4vw, 2rem)", color: "#f1f5f9" }}>
                API Monitoring Dashboard
              </h1>
            </div>
            <p style={{ paddingLeft: "1rem", fontSize: "0.85rem", color: T.muted }}>
              Real-time latency percentiles · auto-refreshes every 5 s
            </p>
          </header>

          {/* ── Controls ── */}
          <form
            onSubmit={handleApply}
            style={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "flex-end",
              gap: "1rem",
              background: T.surface,
              border: `1px solid ${T.border}`,
              borderRadius: "var(--radius-card)",
              padding: "1.25rem 1.5rem",
            }}
          >
            {/* Endpoint ID */}
            <div style={{ flex: "1 1 200px", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
              <label htmlFor="endpoint-input" style={{ fontSize: "0.7rem", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: T.muted }}>
                Endpoint ID
              </label>
              <input
                id="endpoint-input"
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="e.g. google-test"
                minLength={1}
                required
                style={{
                  background: "rgba(255,255,255,0.04)",
                  border: `1px solid ${T.border}`,
                  borderRadius: "0.6rem",
                  padding: "0.55rem 0.9rem",
                  fontSize: "0.9rem",
                  color: "#f1f5f9",
                  outline: "none",
                  width: "100%",
                  transition: "border-color 0.2s",
                }}
                onFocus={(e) => (e.target.style.borderColor = "#6366f1")}
                onBlur={(e) => (e.target.style.borderColor = T.border)}
              />
            </div>

            {/* Time window */}
            <div style={{ width: "9rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
              <label htmlFor="window-select" style={{ fontSize: "0.7rem", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: T.muted }}>
                Window
              </label>
              <select
                id="window-select"
                value={minutes}
                onChange={(e) => setMinutes(Number(e.target.value))}
                style={{
                  background: "#0d1321",
                  border: `1px solid ${T.border}`,
                  borderRadius: "0.6rem",
                  padding: "0.55rem 0.75rem",
                  fontSize: "0.9rem",
                  color: "#f1f5f9",
                  outline: "none",
                  cursor: "pointer",
                  width: "100%",
                }}
              >
                {[1, 5, 15, 30, 60, 240].map((m) => (
                  <option key={m} value={m}>
                    {m >= 60 ? `${m / 60}h` : `${m}m`}
                  </option>
                ))}
              </select>
            </div>

            {/* Apply button */}
            <button
              type="submit"
              style={{
                background: "#6366f1",
                border: "none",
                borderRadius: "0.6rem",
                padding: "0.575rem 1.5rem",
                fontSize: "0.9rem",
                fontWeight: 600,
                color: "#fff",
                cursor: "pointer",
                transition: "background 0.15s, transform 0.1s",
                flexShrink: 0,
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#4f46e5")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "#6366f1")}
              onMouseDown={(e) => (e.currentTarget.style.transform = "scale(0.97)")}
              onMouseUp={(e) => (e.currentTarget.style.transform = "scale(1)")}
            >
              Apply
            </button>

            {/* Live status */}
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center" }}>
              <StatusBadge loading={loading} error={error} lastUpdated={lastUpdated} />
            </div>
          </form>

          {/* ── Error banner ── */}
          {error && (
            <div
              role="alert"
              style={{
                background: "rgba(239,68,68,0.08)",
                border: "1px solid rgba(239,68,68,0.22)",
                borderRadius: "0.75rem",
                padding: "0.9rem 1.25rem",
                fontSize: "0.875rem",
                color: "#fca5a5",
              }}
            >
              ⚠ {error}
            </div>
          )}

          {/* ── Latency percentile cards ── */}
          <section aria-labelledby="latency-heading">
            <SectionHeading>
              <span id="latency-heading">Latency Percentiles</span>
            </SectionHeading>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(14rem, 1fr))", gap: "1rem" }}>
              <MetricCard label="P50 — Median" value={fmt(metrics?.p50)} accent="#6366f1" note="Typical response time" />
              <MetricCard label="P95" value={fmt(metrics?.p95)} accent="#a855f7" note="95th percentile" />
              <MetricCard label="P99 — Tail" value={fmt(metrics?.p99)} accent="#ec4899" note="Worst-case latency" />
            </div>
          </section>

          {/* ── Traffic & health cards ── */}
          <section aria-labelledby="traffic-heading">
            <SectionHeading>
              <span id="traffic-heading">Traffic &amp; Health</span>
            </SectionHeading>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(14rem, 1fr))", gap: "1rem" }}>
              <MetricCard
                label="Request Count"
                value={metrics?.request_count ?? null}
                unit="req"
                accent="#06b6d4"
                note={`Over the last ${windowLabel}`}
              />
              <MetricCard
                label="Error Rate"
                value={fmt(metrics ? metrics.error_rate * 100 : null)}
                unit="%"
                accent={metrics?.error_rate > 0.05 ? "#ef4444" : "#10b981"}
                note={metrics?.error_rate > 0.05 ? "⚠ Above 5 % threshold" : "Within healthy range"}
              />
            </div>
          </section>

          {/* ── Latency chart ── */}
          <section aria-labelledby="chart-heading">
            <SectionHeading>
              <span id="chart-heading">Latency Timeline</span>
            </SectionHeading>
            <LatencyChart data={history} />
          </section>

          {/* ── Empty state ── */}
          {!metrics && !loading && !error && (
            <div
              style={{
                textAlign: "center",
                padding: "4rem 1rem",
                background: T.surface,
                border: `1px solid ${T.border}`,
                borderRadius: "var(--radius-card)",
                color: T.muted,
                fontSize: "0.9rem",
              }}
            >
              Enter an endpoint ID and click <strong style={{ color: "#818cf8" }}>Apply</strong> to load metrics.
            </div>
          )}

          {/* ── Footer ── */}
          <footer style={{ textAlign: "center", fontSize: "0.75rem", color: T.faint }}>
            Monitoring <span style={{ color: T.muted }}>{endpointId}</span> · refreshes every 5 s
          </footer>

        </div>
      </main>
    </>
  );
}
