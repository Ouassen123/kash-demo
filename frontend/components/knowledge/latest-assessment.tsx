import { KnowledgeAssessmentSummary } from '@/lib/types';

export function LatestKnowledgeAssessment({ assessment }: { assessment: KnowledgeAssessmentSummary | null }) {
  if (!assessment) {
    return (
      <section className="glass-panel p-6">
        <p className="text-sm text-white/70">No knowledge assessments yet. Run a CV analysis to get started.</p>
      </section>
    );
  }

  return (
    <section className="glass-panel p-6 flex flex-col gap-4">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Latest assessment</p>
        <p className="text-2xl font-semibold mt-1 text-white">{assessment.assessment_name}</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Score</p>
          <p className="text-4xl font-semibold mt-1">{assessment.normalized_score ? Math.round(assessment.normalized_score) : '—'}</p>
          <p className="text-xs text-white/60">Confidence {assessment.confidence_score ? Math.round(assessment.confidence_score * 100) : 0}%</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Signals</p>
          <p className="text-sm text-white/70 mt-1">{assessment.total_skills_found} skills, {assessment.occupations_suggested} occupations</p>
          <p className="text-xs text-white/60">Experience: {assessment.experience_years.toFixed(1)} yrs</p>
        </div>
      </div>
    </section>
  );
}
