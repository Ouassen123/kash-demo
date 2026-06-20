import { RecommendationItem } from '@/lib/types';
import { Lightbulb, ExternalLink } from 'lucide-react';

const priorityAccent: Record<RecommendationItem['priority'], string> = {
  high: 'border-rose-400/40 bg-rose-500/5 text-rose-50',
  medium: 'border-amber-400/40 bg-amber-500/5 text-amber-50',
  low: 'border-mist/40 bg-white/5 text-mist',
};

export function RecommendationsPanel({ items }: { items: RecommendationItem[] }) {
  return (
    <section className="glass-panel p-6 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Next best moves</p>
          <p className="text-2xl font-semibold mt-1">Personalized actions</p>
        </div>
        <span className="text-xs text-white/60">Ranked by impact</span>
      </div>
      <div className="flex flex-col gap-3">
        {items.map((item, index) => (
          <article key={`${item.text}-${index}`} className="rounded-3xl border border-white/10 bg-white/2 p-4">
            <div className="flex items-start gap-4">
              <span className={`rounded-2xl border px-3 py-1 text-xs font-semibold ${priorityAccent[item.priority]}`}>
                {item.priority.toUpperCase()}
              </span>
              <div className="flex-1">
                <div className="flex items-center gap-2 text-white/80">
                  <Lightbulb size={16} className="text-aurora" />
                  <p className="font-semibold">{item.text}</p>
                </div>
                <p className="text-sm text-white/60 mt-1">Source: {item.source}</p>
              </div>
              <button className="rounded-full border border-white/15 p-2 text-white/70 hover:text-white hover:border-white/40 transition">
                <ExternalLink size={16} />
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
