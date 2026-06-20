import Link from 'next/link';

import { fetchAbilitiesProfile } from '@/lib/api';
import { buildAbilitiesDeepDiveView } from '@/lib/abilities-view';
import { AbilitiesHero } from '@/components/abilities/abilities-hero';
import { AbilitiesAssessmentRunner } from '@/components/abilities/assessment-runner';
import { DomainScoresGrid } from '@/components/abilities/domain-scores';
import { AbilitiesRecommendations } from '@/components/abilities/recommendations';
import { AbilitiesRecentActivity } from '@/components/abilities/recent-activity';

async function loadAbilitiesProfile() {
  try {
    const profile = await fetchAbilitiesProfile();
    return buildAbilitiesDeepDiveView(profile);
  } catch (error) {
    console.error('Failed to load abilities profile', error);
    return buildAbilitiesDeepDiveView(null);
  }
}

export default async function AbilitiesDeepDivePage() {
  const view = await loadAbilitiesProfile();

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

      <AbilitiesHero data={view.hero} />

      <AbilitiesAssessmentRunner />

      <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <DomainScoresGrid scores={view.domainScores} />
        <AbilitiesRecommendations recommendations={view.recommendations} />
      </section>

      <AbilitiesRecentActivity items={view.recentActivity} />
    </main>
  );
}
