import { RecommendationHistoryItem } from '@/lib/intelligence-view';

export function RecommendationHistoryPanel({ items }: { items: RecommendationHistoryItem[] }) {
  if (!items.length) {
    return (
      <section className="glass-panel p-6">
        <p className="text-sm text-white/70">No recommendations recorded yet.</p>
      </section>
    );
  }

  return (
    <section className="glass-panel p-6 space-y-5">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Recommendations</p>
        <p className="text-2xl font-semibold mt-1">History & priority</p>
      </div>
      <div className="space-y-3">
        {items.map((item, idx) => (
          <article key={`${item.text}-${idx}`} className="rounded-3xl border border-white/10 bg-white/3 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-white/85 text-sm">{item.text}</p>
              <span
                className={`text-xs font-semibold uppercase tracking-[0.2em] px-3 py-1 rounded-full border ${
                  item.priority === 'high'
                    ? 'text-rose-200 border-rose-400/40'
                    : item.priority === 'low'
                    ? 'text-mist/80 border-white/20'
                    : 'text-amber-200 border-amber-400/40'
                }`}
              >
                {item.priority}
              </span>
            </div>
            {item.date && <p className="text-xs text-white/60 mt-2">Issued {new Date(item.date).toLocaleDateString()}</p>}
          </article>
        ))}
      </div>
    </section>
  );
}
