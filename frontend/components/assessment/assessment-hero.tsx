import { stageTaglines } from '@/lib/dashboard';
import { IntelligenceAssessmentDetail } from '@/lib/types';
import { BadgeCheck, Clock4 } from 'lucide-react';

interface AssessmentHeroProps {
  assessment: IntelligenceAssessmentDetail;
}

function formatDate(value?: string | null) {
  if (!value) return 'Not available';
  try {
    return new Date(value).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    return value;
  }
}

const statusTokens: Record<string, { label: string; className: string }> = {
  completed: { label: 'Completed', className: 'bg-emerald-500/10 text-emerald-200 border-emerald-400/30' },
  in_progress: { label: 'In progress', className: 'bg-amber-500/10 text-amber-100 border-amber-400/30' },
  pending: { label: 'Pending', className: 'bg-white/5 text-white/70 border-white/20' },
  failed: { label: 'Failed', className: 'bg-rose-500/10 text-rose-100 border-rose-400/30' },
  expired: { label: 'Expired', className: 'bg-white/5 text-white/70 border-white/20' },
};

export function AssessmentHero({ assessment }: AssessmentHeroProps) {
  const { kash_score: score } = assessment;
  const stage = score.career_stage ?? 'explorer';
  const stageTagline = stageTaglines[stage] ?? stageTaglines.explorer;
  const statusToken = statusTokens[assessment.status] ?? statusTokens.completed;

  return (
    <section className="glass-panel relative overflow-hidden">
      <div className="absolute inset-0 opacity-70" style={{ background: 'radial-gradient(circle at top, rgba(74,227,181,0.2), transparent 55%)' }} />
      <div className="relative z-10 grid gap-6 p-6 md:grid-cols-[2fr,1fr]">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Assessment</p>
              <h1 className="text-3xl font-semibold mt-2">{assessment.assessment_name}</h1>
            </div>
            <span className={`border px-4 py-1 rounded-full text-xs font-semibold ${statusToken.className}`}>
              {statusToken.label}
            </span>
          </div>

          <div className="flex items-baseline gap-3">
            <span className="text-6xl font-semibold tracking-tight">{Math.round(score.overall_score)}</span>
            <span className="text-white/60">/ 100 overall</span>
          </div>

          <p className="text-lg text-white/75 leading-relaxed">{stageTagline}</p>

          <div className="flex flex-wrap gap-3 text-sm text-white/70">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/15 px-3 py-1">
              <BadgeCheck size={16} className="text-aurora" />
              <span className="capitalize">{stage} stage</span>
            </div>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/15 px-3 py-1">
              <Clock4 size={16} className="text-mist" />
              <span>Confidence {Math.round(score.confidence * 100)}%</span>
            </div>
            {assessment.industry && (
              <div className="inline-flex items-center gap-2 rounded-full border border-white/15 px-3 py-1">
                <span className="text-white/60">Industry</span>
                <span className="text-white font-medium capitalize">{assessment.industry}</span>
              </div>
            )}
          </div>
        </div>

        <div className="rounded-3xl bg-white/5 border border-white/10 p-5 flex flex-col gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Created</p>
            <p className="text-sm text-white/80 mt-1">{formatDate(assessment.created_at)}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Completed</p>
            <p className="text-sm text-white/80 mt-1">{formatDate(assessment.completed_at)}</p>
          </div>
          {assessment.career_goals?.length ? (
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-white/50">Career goals</p>
              <p className="text-sm text-white/80 mt-1 capitalize">{assessment.career_goals.join(', ')}</p>
            </div>
          ) : null}
          {assessment.custom_weights ? (
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-white/50">Custom weights</p>
              <div className="flex flex-wrap gap-2 mt-2 text-xs text-white/70">
                {Object.entries(assessment.custom_weights).map(([key, value]) => (
                  <span key={key} className="rounded-full border border-white/15 px-2 py-0.5">
                    {key}: {(value * 100).toFixed(0)}%
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
