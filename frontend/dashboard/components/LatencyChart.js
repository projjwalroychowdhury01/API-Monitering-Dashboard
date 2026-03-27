"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

// ─── Custom Tooltip ──────────────────────────────────────────────────────────

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-white/10 bg-[#0d1321]/90 backdrop-blur-md px-4 py-3 text-xs shadow-xl">
      <p className="mb-2 font-semibold text-slate-300">{label}</p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center gap-2 py-0.5">
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{ background: entry.color }}
          />
          <span className="text-slate-400">{entry.name}:</span>
          <span className="font-bold text-white">
            {Number(entry.value).toFixed(2)} ms
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── LatencyChart ─────────────────────────────────────────────────────────────

/**
 * Renders a time-series line chart for p50, p95, p99 latency.
 *
 * @param {{ data: Array<{ time: string, p50: number, p95: number, p99: number }> }} props
 */
export default function LatencyChart({ data = [] }) {
  const isEmpty = !data || data.length === 0;

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md p-6 shadow-lg">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-white">
            Latency Over Time
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            p50 · p95 · p99 — updated every 5 s
          </p>
        </div>
        <span className="text-xs text-slate-600">
          {data.length} sample{data.length !== 1 ? "s" : ""}
        </span>
      </div>

      {isEmpty ? (
        <div className="flex h-48 items-center justify-center text-sm text-slate-600">
          Waiting for data…
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <LineChart
            data={data}
            margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.05)"
            />
            <XAxis
              dataKey="time"
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${v}ms`}
              width={52}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: "12px", paddingTop: "12px" }}
              formatter={(value) => (
                <span style={{ color: "#94a3b8" }}>{value}</span>
              )}
            />
            <Line
              type="monotone"
              dataKey="p50"
              name="P50"
              stroke="#6366f1"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0 }}
            />
            <Line
              type="monotone"
              dataKey="p95"
              name="P95"
              stroke="#a855f7"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0 }}
            />
            <Line
              type="monotone"
              dataKey="p99"
              name="P99"
              stroke="#ec4899"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
