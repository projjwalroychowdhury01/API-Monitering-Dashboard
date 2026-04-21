"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type HistoryPoint = {
  timestamp: string;
  p50: number;
  p95: number;
  p99: number;
};

export function LatencyHistoryChart({ data }: { data: HistoryPoint[] }) {
  if (!data.length) {
    return <div className="empty-state">Waiting for latency history…</div>;
  }

  const chartData = data.map((point) => ({
    ...point,
    label: new Date(point.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  }));

  return (
    <div className="chart-shell">
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <defs>
            <linearGradient id="p95Gradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#005eb8" stopOpacity={0.32} />
              <stop offset="100%" stopColor="#005eb8" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="p99Gradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#609efc" stopOpacity={0.2} />
              <stop offset="100%" stopColor="#609efc" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(118,124,126,0.16)" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: "#5a6062", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "#5a6062", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{
              border: "1px solid rgba(118,124,126,0.16)",
              borderRadius: "16px",
              background: "rgba(247,249,252,0.94)",
              boxShadow: "0 18px 50px rgba(19, 33, 68, 0.14)",
            }}
          />
          <Area type="monotone" dataKey="p95" stroke="#005eb8" fill="url(#p95Gradient)" strokeWidth={2.5} />
          <Area type="monotone" dataKey="p99" stroke="#609efc" fill="url(#p99Gradient)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
