import { Insight } from '@/lib/types';

const priorityTokens: Record<Insight['priority'], { label: string; color: string }> = {
  high: { label: 'High impact', color: 'text-rose-300 bg-rose-500/10' },
  medium: { label: 'Momentum', color: 'text-amber-300 bg-amber-500/10' },
  low: { label: 'Monitor', color: 'text-mist/70 bg-white/5' },
};

export function InsightsPanel({ insights }: { insights: Insight[] }) {
  return (
    <section className="glass-panel p-6 flex flex-col gap-4">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Insights</p>
        <p className="text-2xl font-semibold mt-1">Signals from latest intelligence run</p>
      </div>
      <div className="flex flex-col gap-4">
        {insights.map((insight, index) => {
          const token = priorityTokens[insight.priority];
          return (
            <article key={`${insight.title}-${index}`} className="rounded-3xl border border-white/10 bg-white/3 p-4">
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <h3 className="text-lg font-semibold text-white/90">{insight.title}</h3>
                <span className={`px-3 py-1 text-xs rounded-full ${token.color}`}>{token.label}</span>
              </div>
              <p className="text-white/70 text-sm leading-relaxed mt-2">{insight.description}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
