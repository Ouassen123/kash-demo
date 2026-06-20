import { CareerPathExplanationItem } from '@/lib/types';
import { Compass } from 'lucide-react';

export function CareerPathsPanel({ items }: { items: CareerPathExplanationItem[] }) {
  if (!items.length) {
    return (
      <section className="glass-panel p-6">
        <p className="text-sm text-white/70">No career path explanations generated for this assessment.</p>
      </section>
    );
  }

  return (
    <section className="glass-panel p-6 space-y-5">
      <div className="flex items-center gap-3">
        <Compass size={18} className="text-aurora" />
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Career intelligence</p>
          <p className="text-2xl font-semibold mt-1">Suggested paths</p>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {items.map((item) => (
          <article key={item.career_path} className="rounded-3xl border border-white/10 bg-white/3 p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-lg font-semibold text-white/90 capitalize">{item.career_path.replace('_', ' ')}</p>
                <p className="text-sm text-white/60">Match score</p>
              </div>
              <span className="text-3xl font-semibold text-emerald-300">{Math.round(item.match_score)}</span>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-white/50">Key factors</p>
              <ul className="mt-2 space-y-1 text-sm text-white/75 list-disc pl-4">
                {item.key_factors.map((factor, idx) => (
                  <li key={`${factor}-${idx}`}>{factor}</li>
                ))}
              </ul>
            </div>
            {item.skill_gaps.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-white/50">Skill gaps</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {item.skill_gaps.map((gap) => (
                    <span key={gap} className="rounded-full border border-white/15 px-3 py-1 text-xs text-rose-200/90">
                      {gap}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {item.development_needs.length > 0 && (
              <div className="text-sm text-white/70">
                <p className="text-xs uppercase tracking-[0.3em] text-white/50 mb-1">Development needs</p>
                <ul className="list-disc pl-4 space-y-1">
                  {item.development_needs.map((need, idx) => (
                    <li key={`${need}-${idx}`}>{need}</li>
                  ))}
                </ul>
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
