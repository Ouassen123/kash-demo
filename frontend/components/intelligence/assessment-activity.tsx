import Link from 'next/link';
import { IntelligenceAssessmentSummaryApi } from '@/lib/types';

export function IntelligenceAssessmentActivity({ assessments }: { assessments: IntelligenceAssessmentSummaryApi[] }) {
  if (!assessments.length) {
    return (
      <section className="glass-panel p-6">
        <p className="text-sm text-white/70">No intelligence assessments completed yet.</p>
      </section>
    );
  }

  return (
    <section className="glass-panel p-6 space-y-4">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Assessments</p>
        <p className="text-2xl font-semibold mt-1">Recent intelligence runs</p>
      </div>
      <div className="space-y-3">
        {assessments.map((assessment) => (
          <article key={assessment.assessment_id} className="rounded-3xl border border-white/10 bg-white/3 p-4">
            <div className="flex items-center justify-between text-sm text-white/80">
              <p className="font-semibold text-white">{assessment.assessment_name}</p>
              <span>{assessment.created_at ? new Date(assessment.created_at).toLocaleDateString() : ''}</span>
            </div>
            <div className="mt-2 flex items-center justify-between text-xs uppercase tracking-[0.2em] text-white/60">
              <span>{assessment.status}</span>
              <span>{assessment.overall_score ? `${Math.round(assessment.overall_score)} pts` : '--'}</span>
            </div>
            <Link
              href={`/intelligence/${assessment.assessment_id}`}
              className="mt-3 inline-flex items-center gap-2 text-sm text-aurora hover:text-white transition"
            >
              View details →
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}
