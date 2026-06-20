interface SkillsHeroProps {
  data: {
    averageScore: number;
    bestScore: number;
    improvementTrend: string;
    totalAssessments: number;
    totalUniqueSkills: number;
    languageDiversity: number;
  };
}

const trendTokens: Record<string, { label: string; accent: string }> = {
  improving: { label: 'Trending up', accent: 'text-emerald-300 bg-emerald-500/10' },
  declining: { label: 'Needs focus', accent: 'text-rose-300 bg-rose-500/10' },
  stable: { label: 'Stable', accent: 'text-mist/80 bg-white/5' },
  insufficient_data: { label: 'Awaiting data', accent: 'text-mist/80 bg-white/5' },
};

export function SkillsHero({ data }: SkillsHeroProps) {
  const trend = trendTokens[data.improvementTrend] ?? trendTokens.stable;

  return (
    <section className="glass-panel p-6 grid gap-6 md:grid-cols-[2fr,1fr]">
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Skills deep dive</p>
            <h1 className="text-3xl font-semibold mt-2">Technical capability snapshot</h1>
          </div>
          <span className={`px-4 py-1 rounded-full text-xs font-semibold border border-white/10 ${trend.accent}`}>
            {trend.label}
          </span>
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
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Unique skills</p>
          <p className="text-3xl font-semibold mt-2">{data.totalUniqueSkills}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Language diversity</p>
          <p className="text-3xl font-semibold mt-2">{data.languageDiversity}</p>
        </div>
      </div>
    </section>
  );
}
