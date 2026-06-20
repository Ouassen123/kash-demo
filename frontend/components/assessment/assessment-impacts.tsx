import { AssessmentImpactItem } from '@/lib/types';
import { Activity } from 'lucide-react';

export function AssessmentImpactsPanel({ items }: { items: AssessmentImpactItem[] }) {
  if (!items.length) {
    return null;
  }

  return (
    <section className="glass-panel p-6 space-y-5">
      <div className="flex items-center gap-3">
        <Activity size={18} className="text-aurora" />
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Contribution sources</p>
          <p className="text-2xl font-semibold mt-1">Assessment impacts</p>
        </div>
      </div>
      <div className="space-y-4">
        {items.map((impact) => (
          <article key={`${impact.assessment_name}-${impact.assessment_type}`} className="rounded-3xl border border-white/10 bg-white/3 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white/90 font-semibold">{impact.assessment_name}</p>
                <p className="text-xs uppercase tracking-[0.3em] text-white/50">{impact.assessment_type}</p>
              </div>
              <span className="text-emerald-300 text-xl font-semibold">{impact.score_contribution.toFixed(1)}</span>
            </div>
            <div className="grid grid-cols-3 gap-3 mt-4 text-sm text-white/70">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-white/50">Confidence impact</p>
                <p className="font-semibold">{Math.round(impact.confidence_impact * 100)}%</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-white/50">Improvement potential</p>
                <p className="font-semibold">{Math.round(impact.improvement_potential)} pts</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-white/50">Contribution</p>
                <p className="font-semibold">{impact.score_contribution.toFixed(1)} pts</p>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
