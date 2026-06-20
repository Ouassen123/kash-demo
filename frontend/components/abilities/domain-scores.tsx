interface DomainScoresProps {
  scores: Array<{ domain: string; score: number }>;
}

const domainColors = ['#4AE3B5', '#8E7CFF', '#FFB347', '#6FB1FC', '#FF7C6E'];

export function DomainScoresGrid({ scores }: DomainScoresProps) {
  const items = scores.length ? scores : [{ domain: 'analytical_reasoning', score: 70 }];

  return (
    <section className="glass-panel p-6 space-y-4">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Cognitive domains</p>
        <p className="text-2xl font-semibold mt-1">Score distribution</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {items.map((item, index) => (
          <article key={item.domain} className="rounded-3xl border border-white/10 bg-white/3 p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-white/85 font-semibold capitalize">{item.domain.replace('_', ' ')}</p>
              <span className="text-3xl font-semibold text-white">{Math.round(item.score)}</span>
            </div>
            <div className="h-2 rounded-full bg-white/10">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${Math.min(item.score, 100)}%`,
                  background: `linear-gradient(90deg, ${domainColors[index % domainColors.length]}, rgba(255,255,255,0.6))`,
                }}
              />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
