'use client';

import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export default function IntelligenceTrendChart({ points }: { points: Array<{ date: string; overall: number }> }) {
  const data = points.length ? points : [{ date: new Date().toISOString(), overall: 0 }];

  return (
    <section className="glass-panel p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Trajectory</p>
          <p className="text-2xl font-semibold mt-1">KASH trend</p>
        </div>
        <span className="text-sm text-white/60">Rolling assessments</span>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 0, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="intelligenceTrend" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8EA6FF" stopOpacity={0.9} />
                <stop offset="95%" stopColor="#8EA6FF" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
            <XAxis dataKey="date" tickFormatter={(value) => new Date(value).toLocaleDateString()} stroke="rgba(255,255,255,0.5)" tickLine={false} axisLine={false} />
            <YAxis domain={[0, 100]} stroke="rgba(255,255,255,0.5)" tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0B1221', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12 }}
              labelFormatter={(value) => new Date(value).toLocaleString()}
              formatter={(value: number) => [`${Math.round(value)} pts`, 'Overall score']}
            />
            <Area type="monotone" dataKey="overall" stroke="#A3B8FF" fill="url(#intelligenceTrend)" strokeWidth={3} dot={{ r: 3, strokeWidth: 2, stroke: '#0B1221', fill: '#A3B8FF' }} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
