'use client';

import {
  AreaChart,
  Area,
  ResponsiveContainer,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';

interface TrendChartProps {
  points: Array<{ date: string; overall: number }>;
}

function formatLabel(date: string) {
  try {
    return new Date(date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch (error) {
    return date;
  }
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-2xl border border-white/10 bg-[#0E1629]/95 px-4 py-3 text-sm shadow-panel">
      <p className="text-white/70">{formatLabel(label)}</p>
      <p className="text-2xl font-semibold text-white">{Math.round(payload[0].value)} pts</p>
      <p className="text-xs text-white/60">KASH overall</p>
    </div>
  );
}

export default function TrendChart({ points }: TrendChartProps) {
  const data = points.length ? points : [{ date: new Date().toISOString(), overall: 0 }];

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Trajectory</p>
          <p className="text-2xl font-semibold mt-1">KASH score trend</p>
        </div>
        <span className="text-sm text-white/60">Rolling 8 assessments</span>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ left: 0, right: 0, top: 10, bottom: 0 }}>
            <defs>
              <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#7C9CFF" stopOpacity={0.9} />
                <stop offset="95%" stopColor="#7C9CFF" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={formatLabel}
              tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tickFormatter={(value) => `${value}`}
              tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              domain={[0, 100]}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.15)', strokeWidth: 1 }} />
            <Area
              type="monotone"
              dataKey="overall"
              stroke="#8EA6FF"
              fill="url(#trendGradient)"
              strokeWidth={3}
              dot={{ stroke: '#8EA6FF', fill: '#0E1629', strokeWidth: 2, r: 4 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
