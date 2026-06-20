import Link from 'next/link';

import { fetchKnowledgeProfile } from '@/lib/api';
import { buildKnowledgeDeepDiveView } from '@/lib/knowledge-view';
import { KnowledgeHero } from '@/components/knowledge/knowledge-hero';
import { SkillCategoryChart } from '@/components/knowledge/skill-category-chart';
import { TopSkillsList } from '@/components/knowledge/top-skills';
import { KnowledgeSkillGapPanel } from '@/components/knowledge/skill-gap-panel';
import { CareerSuggestionsPanel } from '@/components/knowledge/career-suggestions';
import { LatestKnowledgeAssessment } from '@/components/knowledge/latest-assessment';

async function loadKnowledgeProfile() {
  try {
    const profile = await fetchKnowledgeProfile();
    return buildKnowledgeDeepDiveView(profile);
  } catch (error) {
    console.error('Failed to load knowledge profile', error);
    return buildKnowledgeDeepDiveView(null);
  }
}

export default async function KnowledgeDeepDivePage() {
  const view = await loadKnowledgeProfile();

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 lg:px-0">
      <div className="flex items-center justify-between gap-3 flex-wrap text-sm text-white/70">
        <Link href="/" className="text-mist hover:text-white transition">
          ← Back to dashboard
        </Link>
        <div className="inline-flex gap-2 text-xs text-white/60">
          <span>Total assessments: {view.hero.totalAssessments}</span>
          <span>• Tracked skills: {view.hero.topSkillCount}</span>
        </div>
      </div>

      <KnowledgeHero data={view.hero} />

      <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <SkillCategoryChart categories={view.skillCategories} />
        <TopSkillsList skills={view.topSkills} />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <KnowledgeSkillGapPanel gaps={view.skillGaps} />
        <CareerSuggestionsPanel suggestions={view.careerSuggestions} />
      </section>

      <LatestKnowledgeAssessment assessment={view.latestAssessment} />

      <section className="glass-panel p-6">
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Learning plan</p>
        <p className="text-2xl font-semibold mt-1">Recommended next steps</p>
        <ul className="mt-4 space-y-2 text-sm text-white/80">
          {view.learningRecommendations.map((rec, idx) => (
            <li key={`${rec}-${idx}`} className="flex items-start gap-2">
              <span className="mt-1 inline-flex h-2 w-2 rounded-full bg-aurora" />
              <span>{rec}</span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
