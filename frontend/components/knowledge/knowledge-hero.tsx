interface KnowledgeHeroProps {
  data: {
    averageScore: number | null;
    totalAssessments: number;
    topSkillCount: number;
    occupationsSuggested: number;
  };
}

export function KnowledgeHero({ data }: KnowledgeHeroProps) {
  return (
    <section className="glass-panel p-6 grid gap-6 md:grid-cols-[2fr,1fr]">
      <div className="flex flex-col gap-6">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Knowledge intelligence</p>
          <h1 className="text-3xl font-semibold mt-2 text-white">CV & taxonomy insights</h1>
          <p className="text-sm text-white/70 mt-2 max-w-2xl">
            Cross-cut view of normalized CV attributes, ESCO mappings, and occupation coverage for employability.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Avg. knowledge score</p>
            <p className="text-4xl font-semibold mt-2">{data.averageScore ? Math.round(data.averageScore) : '—'}</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Assessments</p>
            <p className="text-4xl font-semibold mt-2">{data.totalAssessments}</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Top skills tracked</p>
            <p className="text-4xl font-semibold mt-2">{data.topSkillCount}</p>
          </div>
        </div>
      </div>
      <div className="rounded-3xl border border-white/10 bg-white/5 p-5 flex flex-col gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Occupation coverage</p>
          <p className="text-3xl font-semibold mt-2">{data.occupationsSuggested}</p>
        </div>
        <p className="text-sm text-white/70">Latest assessments referencing ESCO profiles and job families.</p>
      </div>
    </section>
  );
}
