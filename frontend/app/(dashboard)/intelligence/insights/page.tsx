import Link from 'next/link';
import dynamic from 'next/dynamic';

import { fetchIntelligenceProfile, fetchIntelligenceAssessments } from '@/lib/api';
import { buildIntelligenceInsightsView } from '@/lib/intelligence-view';
import { InsightsHero } from '@/components/intelligence/insights-hero';
import { IntelligenceFeatureImportance } from '@/components/intelligence/feature-importance';
import { IntelligenceStrengthsPanel } from '@/components/intelligence/strengths-panel';
import { CareerInsightsPanel } from '@/components/intelligence/career-insights';
import { RecommendationHistoryPanel } from '@/components/intelligence/recommendation-history';
import { IntelligenceAssessmentActivity } from '@/components/intelligence/assessment-activity';

const IntelligenceTrendChart = dynamic(
  () => import('@/components/intelligence/trend-chart'),
  {
    ssr: false,
    loading: () => <div className="glass-panel h-64 animate-pulse" />,
  }
);

async function loadInsights() {
  try {
    const [profile, assessments] = await Promise.all([
      fetchIntelligenceProfile(),
      fetchIntelligenceAssessments(5),
    ]);

    return buildIntelligenceInsightsView(profile, assessments);
  } catch (error) {
    console.error('Failed to load intelligence insights', error);
    return buildIntelligenceInsightsView();
  }
}

export default async function IntelligenceInsightsPage() {
  const view = await loadInsights();

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 lg:px-0">
      <div className="flex items-center justify-between gap-3 flex-wrap text-sm text-white/70">
        <Link href="/" className="text-mist hover:text-white transition">
          ← Back to dashboard
        </Link>
        <div className="inline-flex gap-2 text-xs text-white/60">
          <span>Total assessments: {view.hero.totalAssessments}</span>
          <span>• Updated {new Date(view.hero.lastUpdated).toLocaleDateString()}</span>
        </div>
      </div>

      <InsightsHero data={view.hero} />

      <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <IntelligenceTrendChart points={view.trendPoints} />
        <IntelligenceFeatureImportance items={view.featureImportance} />
      </section>

      <IntelligenceStrengthsPanel strengths={view.strengths} improvementAreas={view.improvementAreas} />

      <CareerInsightsPanel insights={view.careerExplanations} />

      <section className="grid gap-6 lg:grid-cols-2">
        <RecommendationHistoryPanel items={view.recommendationHistory} />
        <IntelligenceAssessmentActivity assessments={view.assessments} />
      </section>
    </main>
  );
}
