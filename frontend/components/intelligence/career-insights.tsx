import { CareerInsightCard } from '@/lib/intelligence-view';

export function CareerInsightsPanel({ insights }: { insights: CareerInsightCard[] }) {
  if (!insights.length) {
    return (
      <section className="glass-panel p-6">
        <p className="text-sm text-white/70">No career insights generated yet.</p>
      </section>
    );
  }

  return (
    <section className="glass-panel p-6 space-y-5">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Career intelligence</p>
        <p className="text-2xl font-semibold mt-1">Alignment highlights</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {insights.map((card) => (
          <article key={card.career_path} className="rounded-3xl border border-white/10 bg-white/3 p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white/90 font-semibold capitalize">{card.career_path.replace('_', ' ')}</p>
                <p className="text-xs text-white/60">Match score</p>
              </div>
              <span className="text-3xl font-semibold text-emerald-300">{Math.round(card.match_score)}</span>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-white/50">Key factors</p>
              <ul className="mt-2 space-y-1 text-sm text-white/75 list-disc pl-4">
                {card.key_factors.map((factor, idx) => (
                  <li key={`${factor}-${idx}`}>{factor}</li>
                ))}
              </ul>
            </div>
            {card.skill_gaps.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-white/50">Skill gaps</p>
                <div className="mt-2 flex flex-wrap gap-2 text-xs text-white/80">
                  {card.skill_gaps.map((gap) => (
                    <span key={gap} className="rounded-full border border-white/15 px-3 py-1">
                      {gap}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
