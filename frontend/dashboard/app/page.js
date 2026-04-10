"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { getLatency } from "../lib/api";
import LatencyChart from "../components/LatencyChart";

// ─── Design tokens (mirror CSS vars for inline styles) ────────────────────────
// Stitch "High-End Editorial Data Experience" — Light mode, primary #005eb8

const T = {
  surface: "rgba(255,255,255,0.04)",
  surfaceHv: "rgba(255,255,255,0.07)",
  border: "rgba(255,255,255,0.08)",
  borderHv: "rgba(255,255,255,0.16)",
  muted: "#64748b",
  faint: "#334155",
};

// ─── MetricCard ───────────────────────────────────────────────────────────────
// Stitch: no divider lines, vertical whitespace instead, surface_container_lowest bg
// Label in label-sm all-caps, value in display-md scale

function MetricCard({ label, value, unit = "ms", accentColor, note, noteWarn = false }) {
  const [hovered, setHovered] = useState(false);

  return (
    <article
      style={{
        background: T.surfaceCard,
        borderRadius: "var(--radius-card, 0.375rem)",
        padding: "1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: 0,
        boxShadow: hovered
          ? "0 12px 32px -4px rgba(45,51,53,0.10)"
          : T.shadow,
        transition: "box-shadow 0.25s ease, transform 0.2s ease",
        transform: hovered ? "translateY(-2px)" : "translateY(0)",
        cursor: "default",
        animation: "fadeIn 0.4s ease both",
        position: "relative",
        overflow: "hidden",
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Accent glow — primary_container at low opacity */}
      {accentColor && (
        <span
          aria-hidden
          style={{
            position: "absolute",
            top: "-1.5rem",
            right: "-1.5rem",
            width: "5rem",
            height: "5rem",
            borderRadius: "9999px",
            background: accentColor,
            opacity: 0.12,
            filter: "blur(28px)",
            pointerEvents: "none",
          }}
        />
      )}

      {/* Label — label-sm, all-caps, 0.05em tracking */}
      <span
        style={{
          fontSize: "var(--text-label, 0.6875rem)",
          fontWeight: 600,
          letterSpacing: "0.05em",
          textTransform: "uppercase",
          color: T.onSurfaceVar,
          marginBottom: "1.5rem",
        }}
      >
        {label}
      </span>

      {/* Value + unit */}
      <div style={{ display: "flex", alignItems: "baseline", gap: "0.3rem", marginBottom: "0.75rem" }}>
        <span
          style={{
            fontSize: value != null ? "var(--text-display, 2.75rem)" : "2rem",
            fontWeight: 700,
            letterSpacing: "-0.03em",
            color: T.onSurface,
            fontVariantNumeric: "tabular-nums",
            lineHeight: 1,
          }}
        >
          {value ?? "—"}
        </span>
        {unit && value != null && (
          <span style={{ fontSize: "0.85rem", color: T.onSurfaceVar, fontWeight: 500 }}>
            {unit}
          </span>
        )}
      </div>

      {/* Note — body-sm, secondary text */}
      {note && (
        <span
          style={{
            fontSize: "0.75rem",
            color: noteWarn ? T.error : T.onSurfaceVar,
            fontWeight: noteWarn ? 600 : 400,
          }}
        >
          {note}
        </span>
      )}
    </article>
  );
}

// ─── SectionLabel ─────────────────────────────────────────────────────────────
// headline-sm for section titles — editorial structure

function SectionLabel({ id, children }) {
  return (
    <h2
      id={id}
      style={{
        fontSize: "var(--text-headline, 1.5rem)",
        fontWeight: 700,
        letterSpacing: "-0.02em",
        color: T.onSurface,
        marginBottom: "1.25rem",
      }}
    >
      {children}
    </h2>
  );
}

// ─── Chip / status pill ───────────────────────────────────────────────────────
// Stitch: secondary_container bg, on_secondary_container text, full radius

function Chip({ loading, error, lastUpdated }) {
  const baseStyle = {
    display: "inline-flex",
    alignItems: "center",
    gap: "0.4rem",
    padding: "0.3rem 0.85rem",
    borderRadius: "var(--radius-chip, 9999px)",
    fontSize: "0.75rem",
    fontWeight: 500,
  };
  const dot = { width: "0.45rem", height: "0.45rem", borderRadius: "9999px", flexShrink: 0 };

  if (error)
    return (
      <span style={{ ...baseStyle, background: "#fa746f22", color: T.error }}>
        <span style={{ ...dot, background: T.error }} /> Error
      </span>
    );

  if (loading)
    return (
      <span style={{ ...baseStyle, background: T.secondaryCont, color: T.onSecondaryCont }}>
        <span style={{ ...dot, background: T.primary, animation: "pulse 1.5s ease-in-out infinite" }} />
        Fetching…
      </span>
    );

  if (lastUpdated)
    return (
      <span style={{ ...baseStyle, background: T.secondaryCont, color: T.onSecondaryCont }}>
        <span style={{ ...dot, background: T.success }} />
        Live · {lastUpdated}
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

  // ── Fetch ──────────────────────────────────────────────────────────────────

  const fetchMetrics = useCallback(async (signal) => {
    if (!endpointId || isFetchingRef.current) return;
    isFetchingRef.current = true;
    setLoading(true);
    setError(null);
    try {
      const data = await getLatency(endpointId, minutes, signal);
      if (signal?.aborted) return;
      setMetrics(data);
      const ts = new Date().toLocaleTimeString();
      setLastUpdated(ts);
      setHistory((prev) => {
        const pt = { time: ts, p50: data.p50, p95: data.p95, p99: data.p99 };
        const next = [...prev, pt];
        return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next;
      });
    } catch (err) {
      if (err.name !== "CanceledError" && err.name !== "AbortError") setError(err.message);
    } finally {
      if (!signal?.aborted) setLoading(false);
      isFetchingRef.current = false;
    }
  }, [endpointId, minutes]);

  // ── Polling ────────────────────────────────────────────────────────────────

  useEffect(() => {
    const ctrl = new AbortController();
    abortCtrlRef.current = ctrl;
    fetchMetrics(ctrl.signal);
    intervalRef.current = setInterval(() => fetchMetrics(ctrl.signal), 5000);
    return () => {
      ctrl.abort();
      clearInterval(intervalRef.current);
      isFetchingRef.current = false;
    };
  }, [fetchMetrics]);

  // ── Helpers ────────────────────────────────────────────────────────────────

  const handleApply = (e) => {
    e.preventDefault();
    setHistory([]);
    setEndpointId(inputValue.trim());
  };

  const fmt = (n, d = 2) => (n != null ? Number(n).toFixed(d) : null);
  const windowLabel = minutes >= 60 ? `${minutes / 60}h` : `${minutes}m`;

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div
      style={{
        minHeight: "100vh",
        background: T.bgBase,
        color: T.onSurface,
      }}
    >
      {/* ── Top navigation bar ── */}
      <nav
        style={{
          background: "rgba(248,249,250,0.8)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          borderBottom: `1px solid ${T.ghostBorder}`,
          padding: "0 2rem",
          height: "3.5rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          position: "sticky",
          top: 0,
          zIndex: 50,
        }}
      >
        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
          {/* Primary accent bar */}
          <span
            style={{
              display: "inline-block",
              width: "0.2rem",
              height: "1.4rem",
              borderRadius: "9999px",
              background: `linear-gradient(180deg, ${T.primary} 0%, ${T.primaryContainer} 100%)`,
              flexShrink: 0,
            }}
          />
          <span
            style={{
              fontSize: "0.95rem",
              fontWeight: 700,
              letterSpacing: "-0.01em",
              color: T.onSurface,
            }}
          >
            Nexus Console
          </span>
        </div>

        {/* Nav chips */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          {["Overview", "Endpoints", "Alerts", "Settings"].map((tab, i) => (
            <button
              key={tab}
              style={{
                padding: "0.25rem 0.85rem",
                borderRadius: "var(--radius-chip, 9999px)",
                fontSize: "0.75rem",
                fontWeight: 500,
                border: "none",
                cursor: "pointer",
                background: i === 0 ? T.secondaryCont : "transparent",
                color: i === 0 ? T.onSecondaryCont : T.onSurfaceVar,
                transition: "background 0.15s",
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </nav>

      {/* ── Page content ── */}
      <main style={{ maxWidth: "72rem", margin: "0 auto", padding: "2.5rem 1.5rem 6rem" }}>

        {/* ── Page header ── */}
        <header style={{ marginBottom: "2.5rem", animation: "fadeIn 0.5s ease both" }}>
          <p
            style={{
              fontSize: "var(--text-label, 0.6875rem)",
              fontWeight: 600,
              letterSpacing: "0.05em",
              textTransform: "uppercase",
              color: T.primary,
              marginBottom: "0.5rem",
            }}
          >
            Executive API Insights
          </p>
          <h1
            style={{
              fontSize: "clamp(1.75rem, 4vw, 2.25rem)",
              fontWeight: 700,
              letterSpacing: "-0.03em",
              color: T.onSurface,
              marginBottom: "0.5rem",
            }}
          >
            API Metrics Dashboard
          </h1>
          <p style={{ fontSize: "var(--text-body, 0.875rem)", color: T.onSurfaceVar }}>
            Performance overview for{" "}
            <span
              style={{
                display: "inline-block",
                padding: "0.1rem 0.6rem",
                borderRadius: "var(--radius-chip, 9999px)",
                background: T.secondaryCont,
                color: T.onSecondaryCont,
                fontSize: "0.75rem",
                fontWeight: 600,
              }}
            >
              {endpointId}
            </span>
          </p>
        </header>

        {/* ── Controls strip ── */}
        <section
          style={{
            background: T.surfaceLow,
            borderRadius: "var(--radius-card, 0.375rem)",
            padding: "1.25rem 1.5rem",
            marginBottom: "2rem",
            animation: "fadeIn 0.55s ease both",
          }}
        >
          <form
            onSubmit={handleApply}
            style={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "flex-end",
              gap: "1rem",
            }}
          >
            {/* Endpoint ID */}
            <div style={{ flex: "1 1 200px", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
              <label
                htmlFor="endpoint-input"
                style={{
                  fontSize: "var(--text-label, 0.6875rem)",
                  fontWeight: 600,
                  letterSpacing: "0.05em",
                  textTransform: "uppercase",
                  color: T.onSurfaceVar,
                }}
              >
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
                  background: T.surfaceHigh,
                  border: `0.125rem solid ${T.ghostBorder}`,
                  borderRadius: "var(--radius-card, 0.375rem)",
                  padding: "0.55rem 0.9rem",
                  fontSize: "var(--text-body, 0.875rem)",
                  color: T.onSurface,
                  outline: "none",
                  width: "100%",
                  transition: "border-color 0.2s, box-shadow 0.2s",
                }}
                onFocus={(e) => (e.target.style.borderColor = "#6366f1")}
                onBlur={(e) => (e.target.style.borderColor = T.border)}
              />
            </div>

            {/* Time window */}
            <div style={{ width: "9rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
              <label
                htmlFor="window-select"
                style={{
                  fontSize: "var(--text-label, 0.6875rem)",
                  fontWeight: 600,
                  letterSpacing: "0.05em",
                  textTransform: "uppercase",
                  color: T.onSurfaceVar,
                }}
              >
                Window
              </label>
              <select
                id="window-select"
                value={minutes}
                onChange={(e) => setMinutes(Number(e.target.value))}
                style={{
                  background: T.surfaceHigh,
                  border: `0.125rem solid ${T.ghostBorder}`,
                  borderRadius: "var(--radius-card, 0.375rem)",
                  padding: "0.55rem 0.75rem",
                  fontSize: "var(--text-body, 0.875rem)",
                  color: T.onSurface,
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

            {/* Apply — gradient CTA (Stitch signature) */}
            <button
              type="submit"
              style={{
                background: `linear-gradient(135deg, ${T.primary} 0%, ${T.primaryContainer} 100%)`,
                border: "none",
                borderRadius: "var(--radius-card, 0.375rem)",
                padding: "0.575rem 1.5rem",
                fontSize: "var(--text-body, 0.875rem)",
                fontWeight: 600,
                color: T.onPrimary,
                cursor: "pointer",
                transition: "opacity 0.15s, transform 0.1s",
                flexShrink: 0,
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#4f46e5")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "#6366f1")}
              onMouseDown={(e) => (e.currentTarget.style.transform = "scale(0.97)")}
              onMouseUp={(e) => (e.currentTarget.style.transform = "scale(1)")}
            >
              Apply
            </button>

            {/* Live status chip */}
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center" }}>
              <Chip loading={loading} error={error} lastUpdated={lastUpdated} />
            </div>
          </form>
        </section>

        {/* ── Error banner ── */}
        {error && (
          <div
            role="alert"
            style={{
              background: "rgba(168,56,54,0.07)",
              border: `0.125rem solid rgba(168,56,54,0.15)`,
              borderRadius: "var(--radius-card, 0.375rem)",
              padding: "0.9rem 1.25rem",
              fontSize: "var(--text-body, 0.875rem)",
              color: T.error,
              marginBottom: "2rem",
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

        {/* ── System Latency chart ── */}
        <section
          aria-labelledby="latency-heading"
          style={{
            background: T.surfaceLow,
            borderRadius: "var(--radius-card, 0.375rem)",
            padding: "1.75rem",
            marginBottom: "2rem",
            animation: "fadeIn 0.65s ease both",
          }}
        >
          <SectionLabel id="latency-heading">System Latency (ms)</SectionLabel>
          <p
            style={{
              fontSize: "var(--text-body, 0.875rem)",
              color: T.onSurfaceVar,
              marginBottom: "1.25rem",
              marginTop: "-0.75rem",
            }}
          >
            Aggregated performance across all nodes · auto-refreshes every 5 s
          </p>
          <LatencyChart data={history} />
        </section>

        {/* ── Recent endpoint activity ── */}
        <section
          aria-labelledby="activity-heading"
          style={{
            background: T.surfaceLow,
            borderRadius: "var(--radius-card, 0.375rem)",
            padding: "1.75rem",
            animation: "fadeIn 0.7s ease both",
          }}
        >
          <SectionLabel id="activity-heading">Recent Endpoint Activity</SectionLabel>
          {history.length === 0 ? (
            <p style={{ fontSize: "var(--text-body, 0.875rem)", color: T.onSurfaceVar }}>
              No activity recorded yet. Polling will populate this table.
            </p>
          ) : (
            <div
              style={{
                background: T.surfaceCard,
                borderRadius: "var(--radius-card, 0.375rem)",
                overflow: "hidden",
                boxShadow: T.shadow,
              }}
            >
              {/* Table header */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 5rem 5rem 5rem",
                  padding: "0.6rem 1.25rem",
                  background: T.surfaceLow,
                }}
              >
                {["Timestamp", "P50", "P95", "P99"].map((h) => (
                  <span
                    key={h}
                    style={{
                      fontSize: "var(--text-label, 0.6875rem)",
                      fontWeight: 600,
                      letterSpacing: "0.05em",
                      textTransform: "uppercase",
                      color: T.onSurfaceVar,
                    }}
                  >
                    {h}
                  </span>
                ))}
              </div>

              {/* Table rows — no divider lines, hover tonal shift */}
              {[...history].reverse().slice(0, 10).map((row, i) => (
                <ActivityRow key={`${row.time}-${i}`} row={row} alt={i % 2 === 1} />
              ))}
            </div>
          )}
        </section>

        {/* ── Empty state ── */}
        {!metrics && !loading && !error && (
          <div
            style={{
              textAlign: "center",
              padding: "4rem 1rem",
              background: T.surfaceLow,
              borderRadius: "var(--radius-card, 0.375rem)",
              color: T.onSurfaceVar,
              fontSize: "var(--text-body, 0.875rem)",
              marginTop: "2rem",
              animation: "fadeIn 0.5s ease both",
            }}
          >
            Enter an endpoint ID and click{" "}
            <strong style={{ color: T.primary }}>Apply</strong> to load metrics.
          </div>
        )}

        {/* ── Footer ── */}
        <footer
          style={{
            marginTop: "3rem",
            textAlign: "center",
            fontSize: "0.75rem",
            color: T.outlineVar,
          }}
        >
          © 2024 Nexus Console · Systems Engine ·{" "}
          <span style={{ color: T.onSurfaceVar }}>Monitoring {endpointId}</span>
        </footer>
      </main>
    </div>
  );
}

// ─── ActivityRow ──────────────────────────────────────────────────────────────
// Stitch: no row dividers, hover → surface_container_high tonal shift

function ActivityRow({ row, alt }) {
  const [hovered, setHovered] = useState(false);
  const fmt = (n) => (n != null ? Number(n).toFixed(2) : "—");

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 5rem 5rem 5rem",
        padding: "0.5rem 1.25rem",
        background: hovered
          ? "rgba(235,238,240,0.7)"
          : alt
            ? "rgba(248,249,250,0.6)"
            : "transparent",
        transition: "background 0.15s",
        fontSize: "var(--text-body, 0.875rem)",
        color: "#2d3335",
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <span style={{ color: "#5a6062", fontVariantNumeric: "tabular-nums" }}>{row.time}</span>
      <span style={{ fontVariantNumeric: "tabular-nums", fontWeight: 500 }}>{fmt(row.p50)}</span>
      <span style={{ fontVariantNumeric: "tabular-nums", fontWeight: 500 }}>{fmt(row.p95)}</span>
      <span style={{ fontVariantNumeric: "tabular-nums", fontWeight: 500 }}>{fmt(row.p99)}</span>
    </div>
  );
}
