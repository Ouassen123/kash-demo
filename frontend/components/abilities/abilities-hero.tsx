interface AbilitiesHeroProps {
  data: {
    averageScore: number;
    bestScore: number;
    totalAssessments: number;
    improvementTrend: string;
  };
}

const trendTokens: Record<string, { label: string; accent: string }> = {
  improving: { label: 'Improving', accent: 'text-emerald-300 bg-emerald-500/10' },
  declining: { label: 'Declining', accent: 'text-rose-300 bg-rose-500/10' },
  stable: { label: 'Stable', accent: 'text-mist/80 bg-white/5' },
  insufficient_data: { label: 'Awaiting data', accent: 'text-mist/80 bg-white/5' },
};

export function AbilitiesHero({ data }: AbilitiesHeroProps) {
  const trend = trendTokens[data.improvementTrend] ?? trendTokens.insufficient_data;

  return (
    <section className="glass-panel p-6 grid gap-6 md:grid-cols-[2fr,1fr]">
      <div className="flex flex-col gap-6">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Abilities intelligence</p>
          <h1 className="text-3xl font-semibold mt-2 text-white">Adaptive assessments snapshot</h1>
          <p className="text-sm text-white/70 mt-2 max-w-2xl">
            View cognitive domain performance across quiz sessions, improvement trend, and top strengths to guide future drills.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Average score</p>
            <p className="text-4xl font-semibold mt-2">{Math.round(data.averageScore)}</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Best score</p>
            <p className="text-4xl font-semibold mt-2">{Math.round(data.bestScore)}</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Assessments</p>
            <p className="text-4xl font-semibold mt-2">{data.totalAssessments}</p>
          </div>
        </div>
      </div>
      <div className="rounded-3xl border border-white/10 bg-white/5 p-5 flex flex-col gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Trend</p>
          <span className={`inline-flex items-center gap-2 px-4 py-1 text-xs font-semibold rounded-full border ${trend.accent}`}>
            {trend.label}
          </span>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Suggested next action</p>
          <p className="text-sm text-white/70 mt-2">Repeat focus domains weekly to keep the adaptive difficulty calibrated.</p>
        </div>
      </div>
    </section>
  );
}
