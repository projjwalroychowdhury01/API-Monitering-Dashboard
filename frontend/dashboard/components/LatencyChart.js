"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

// Stitch palette — light mode
const PRIMARY        = "#005eb8";
const PRIMARY_CONT   = "#609efc";
const TERTIARY       = "#665882";
const ON_SURFACE_VAR = "#5a6062";
const SURFACE_CARD   = "#ffffff";
const SURFACE_LOW    = "#f1f4f5";
const OUTLINE_VAR    = "#adb3b5";

// ─── Custom Tooltip ──────────────────────────────────────────────────────────
// Stitch: glassmorphism for floating elements — surface at 80% opacity + blur

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "rgba(248,249,250,0.85)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        border: "0.125rem solid rgba(173,179,181,0.15)",   // ghost border
        borderRadius: "0.375rem",
        padding: "0.75rem 1rem",
        fontSize: "0.75rem",
        boxShadow: "0 0 24px 0 rgba(45,51,53,0.08)",        // ambient shadow
        minWidth: "10rem",
      }}
    >
      <p
        style={{
          marginBottom: "0.5rem",
          fontWeight: 600,
          color: "#5a6062",
          letterSpacing: "0.05em",
          textTransform: "uppercase",
          fontSize: "0.6875rem",
        }}
      >
        {label}
      </p>
      {payload.map((entry) => (
        <div
          key={entry.dataKey}
          style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.2rem 0" }}
        >
          <span
            style={{
              display: "inline-block",
              width: "0.5rem",
              height: "0.5rem",
              borderRadius: "9999px",
              background: entry.color,
              flexShrink: 0,
            }}
          />
          <span style={{ color: ON_SURFACE_VAR }}>{entry.name}:</span>
          <span style={{ fontWeight: 700, color: "#2d3335", fontVariantNumeric: "tabular-nums" }}>
            {Number(entry.value).toFixed(2)} ms
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── LatencyChart ─────────────────────────────────────────────────────────────
// Area chart: primary line + gradient fill fading to 0% (Stitch data viz rule)

export default function LatencyChart({ data = [] }) {
  const isEmpty = !data || data.length === 0;

  return (
    <div
      style={{
        background: SURFACE_CARD,
        borderRadius: "0.375rem",
        padding: "1.5rem",
        boxShadow: "0 12px 32px -4px rgba(45,51,53,0.06)",
      }}
    >
      {/* Card header */}
      <div style={{ marginBottom: "1.25rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h3
            style={{
              fontSize: "var(--text-title, 1.125rem)",
              fontWeight: 600,
              color: "#2d3335",
              marginBottom: "0.25rem",
            }}
          >
            Latency Over Time
          </h3>
          <p style={{ fontSize: "0.6875rem", color: ON_SURFACE_VAR, letterSpacing: "0.05em", textTransform: "uppercase", fontWeight: 600 }}>
            P50 · P95 · P99
          </p>
        </div>
        <span
          style={{
            padding: "0.2rem 0.7rem",
            borderRadius: "9999px",
            background: "#d9e3f9",
            color: "#495264",
            fontSize: "0.75rem",
            fontWeight: 500,
          }}
        >
          {data.length} sample{data.length !== 1 ? "s" : ""}
        </span>
      </div>

      {isEmpty ? (
        <div
          style={{
            height: "12rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: SURFACE_LOW,
            borderRadius: "0.375rem",
            color: ON_SURFACE_VAR,
            fontSize: "0.875rem",
          }}
        >
          Waiting for data…
        </div>
      ) : (
        <>
          {/* SVG gradient defs */}
          <svg width="0" height="0" style={{ position: "absolute" }}>
            <defs>
              <linearGradient id="grad-p50" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%"   stopColor={PRIMARY}      stopOpacity="0.20" />
                <stop offset="100%" stopColor={PRIMARY}      stopOpacity="0" />
              </linearGradient>
              <linearGradient id="grad-p95" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%"   stopColor={PRIMARY_CONT} stopOpacity="0.15" />
                <stop offset="100%" stopColor={PRIMARY_CONT} stopOpacity="0" />
              </linearGradient>
              <linearGradient id="grad-p99" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%"   stopColor={TERTIARY}     stopOpacity="0.12" />
                <stop offset="100%" stopColor={TERTIARY}     stopOpacity="0" />
              </linearGradient>
            </defs>
          </svg>

          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
              {/* Grid — outline_variant at 10 % (Stitch data viz rule) */}
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={`${OUTLINE_VAR}1A`}   /* 10 % opacity hex suffix */
                vertical={false}
              />
              <XAxis
                dataKey="time"
                tick={{ fill: ON_SURFACE_VAR, fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fill: ON_SURFACE_VAR, fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `${v}ms`}
                width={52}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: "12px", paddingTop: "12px" }}
                formatter={(value) => (
                  <span style={{ color: ON_SURFACE_VAR, fontWeight: 500 }}>{value}</span>
                )}
              />

              {/* P50 — primary */}
              <Area
                type="monotone"
                dataKey="p50"
                name="P50"
                stroke={PRIMARY}
                strokeWidth={2}
                fill="url(#grad-p50)"
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0, fill: PRIMARY }}
              />

              {/* P95 — primary_container */}
              <Area
                type="monotone"
                dataKey="p95"
                name="P95"
                stroke={PRIMARY_CONT}
                strokeWidth={2}
                fill="url(#grad-p95)"
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0, fill: PRIMARY_CONT }}
              />

              {/* P99 — tertiary */}
              <Area
                type="monotone"
                dataKey="p99"
                name="P99"
                stroke={TERTIARY}
                strokeWidth={2}
                fill="url(#grad-p99)"
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0, fill: TERTIARY }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </>
      )}
    </div>
  );
}
