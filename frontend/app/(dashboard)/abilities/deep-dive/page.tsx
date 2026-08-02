import Link from 'next/link';

import { fetchAttitudeProfile } from '@/lib/api';
import { buildAttitudeDeepDiveView } from '@/lib/abilities-view';
import { AttitudeHero } from '@/components/abilities/abilities-hero';
import { AttitudeAssessmentRunner } from '@/components/abilities/assessment-runner';
import { DomainScoresGrid } from '@/components/abilities/domain-scores';
import { AttitudeRecommendations } from '@/components/abilities/recommendations';
import { AttitudeRecentActivity } from '@/components/abilities/recent-activity';

async function loadAttitudeProfile() {
  try {
    const profile = await fetchAttitudeProfile();
    return buildAttitudeDeepDiveView(profile);
  } catch (error) {
    console.error('Failed to load attitude profile', error);
    return buildAttitudeDeepDiveView(null);
  }
}

export default async function AttitudeDeepDivePage() {
  const view = await loadAttitudeProfile();

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 lg:px-0">
      <div className="flex items-center justify-between gap-3 flex-wrap text-sm text-white/70">
        <Link href="/" className="text-mist hover:text-white transition">
          ← Back to dashboard
        </Link>
        <div className="inline-flex gap-2 text-xs text-white/60">
          <span>Total assessments: {view.hero.totalAssessments}</span>
          <span>• Trend: {view.hero.improvementTrend}</span>
        </div>
      </div>

      <AttitudeHero data={view.hero} />

      <AttitudeAssessmentRunner />

      <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <DomainScoresGrid scores={view.domainScores} />
        <AttitudeRecommendations recommendations={view.recommendations} />
      </section>

      <AttitudeRecentActivity items={view.recentActivity} />
    </main>
  );
}
