import Link from 'next/link';
import { notFound } from 'next/navigation';

import { fetchIntelligenceAssessment } from '@/lib/api';
import { AssessmentHero } from '@/components/assessment/assessment-hero';
import { ScoreBreakdown } from '@/components/assessment/score-breakdown';
import { FeatureImportanceChart } from '@/components/assessment/feature-importance';
import { CareerPathsPanel } from '@/components/assessment/career-paths';
import { SkillGapPanel } from '@/components/assessment/skill-gap-panel';
import { AssessmentImpactsPanel } from '@/components/assessment/assessment-impacts';

async function loadAssessment(assessmentId: string) {
  try {
    const data = await fetchIntelligenceAssessment(assessmentId);
    return data;
  } catch (error) {
    console.error('Failed to load assessment detail', error);
    return null;
  }
}

export default async function AssessmentDetailPage({ params }: { params: { assessmentId: string } }) {
  const assessment = await loadAssessment(params.assessmentId);

  if (!assessment) {
    notFound();
  }

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 lg:px-0">
      <div className="flex items-center gap-3 text-sm text-white/70">
        <Link href="/" className="text-mist hover:text-white transition">
          ← Back to dashboard
        </Link>
        <span>/</span>
        <span className="text-white">Assessment detail</span>
      </div>

      <AssessmentHero assessment={assessment} />

      <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <ScoreBreakdown assessment={assessment} />
        <FeatureImportanceChart items={assessment.feature_importance} />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <CareerPathsPanel items={assessment.career_explanations} />
        <SkillGapPanel analysis={assessment.skill_gap_analysis} />
      </section>

      <AssessmentImpactsPanel items={assessment.assessment_impacts} />
    </main>
  );
}
