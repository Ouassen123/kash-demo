import { IntelligenceAssessmentDetail } from '@/lib/types';
import { Fragment } from 'react';

const domainTokens = [
  { key: 'knowledge', label: 'Knowledge', gradient: 'from-[#4AE3B5] to-[#178F66]' },
  { key: 'abilities', label: 'Abilities', gradient: 'from-[#8E7CFF] to-[#4C3BCE]' },
  { key: 'skills', label: 'Skills', gradient: 'from-[#FFB347] to-[#FF7C6E]' },
  { key: 'experience', label: 'Experience', gradient: 'from-[#6FB1FC] to-[#365CFF]' },
] as const;

export function ScoreBreakdown({ assessment }: { assessment: IntelligenceAssessmentDetail }) {
  const { kash_score } = assessment;

  const domainScores = domainTokens.map((domain) => {
    const value = kash_score[`${domain.key}_score` as keyof typeof kash_score] as number;
    return { ...domain, value };
  });

  return (
    <section className="glass-panel p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-mist/70">KASH breakdown</p>
          <p className="text-2xl font-semibold mt-1">Domain scores</p>
        </div>
        <span className="text-sm text-white/60">Confidence {Math.round(kash_score.confidence * 100)}%</span>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {domainScores.map((domain) => (
          <article key={domain.key} className="rounded-3xl border border-white/10 bg-white/3 p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-white/70">{domain.label}</p>
              <span className="text-2xl font-semibold">{Math.round(domain.value)}</span>
            </div>
            <div className="h-2 rounded-full bg-white/10">
              <div
                className={`h-full rounded-full bg-gradient-to-r ${domain.gradient}`}
                style={{ width: `${Math.min(domain.value, 100)}%` }}
              />
            </div>
          </article>
        ))}
      </div>
      {(kash_score.strengths?.length || kash_score.improvement_areas?.length) && (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Strengths</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {kash_score.strengths?.map((item) => (
                <span key={item} className="rounded-full border border-white/15 px-3 py-1 text-xs text-emerald-200/90">
                  {item}
                </span>
              )) || <span className="text-sm text-white/50">Not available</span>}
            </div>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Improvement areas</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {kash_score.improvement_areas?.map((item) => (
                <span key={item} className="rounded-full border border-white/15 px-3 py-1 text-xs text-rose-200/90">
                  {item}
                </span>
              )) || <span className="text-sm text-white/50">Not available</span>}
            </div>
          </div>
        </div>
      )}
      {assessment.kash_score.recommendations?.length ? (
        <div className="mt-6">
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">System recommendations</p>
          <ul className="mt-2 space-y-2 text-sm text-white/75">
            {assessment.kash_score.recommendations.map((rec, idx) => (
              <Fragment key={`${rec}-${idx}`}>
                <li className="flex items-start gap-2">
                  <span className="mt-1 inline-flex h-2 w-2 rounded-full bg-aurora" />
                  <span>{rec}</span>
                </li>
              </Fragment>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
