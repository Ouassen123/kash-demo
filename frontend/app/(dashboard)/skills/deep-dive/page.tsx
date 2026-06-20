import Link from 'next/link';
import { notFound } from 'next/navigation';

import { fetchSkillsProfile } from '@/lib/api';
import { buildSkillsDeepDiveView } from '@/lib/skills-view';
import { SkillsHero } from '@/components/skills/skills-hero';
import { LanguageMix } from '@/components/skills/language-mix';
import { ProficiencyDistribution } from '@/components/skills/proficiency-distribution';
import { CategoryGrid } from '@/components/skills/category-grid';
import { ProjectTimeline } from '@/components/skills/project-timeline';
import { SkillsRecommendations } from '@/components/skills/recommendations';
import { RecentActivityList } from '@/components/skills/recent-activity';

async function loadSkillsProfile() {
  try {
    const profile = await fetchSkillsProfile();
    return buildSkillsDeepDiveView(profile);
  } catch (error) {
    console.error('Failed to load skills profile', error);
    return buildSkillsDeepDiveView(null);
  }
}

export default async function SkillsDeepDivePage() {
  const view = await loadSkillsProfile();

  if (!view) {
    notFound();
  }

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 lg:px-0">
      <div className="flex items-center justify-between gap-3 flex-wrap text-sm text-white/70">
        <Link href="/" className="text-mist hover:text-white transition">
          ← Back to dashboard
        </Link>
        <div className="inline-flex gap-2 text-xs text-white/60">
          <span>Total assessments: {view.hero.totalAssessments}</span>
          <span>• Unique skills: {view.hero.totalUniqueSkills}</span>
        </div>
      </div>

      <SkillsHero data={view.hero} />

      <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <LanguageMix languages={view.languages} />
        <ProficiencyDistribution data={view.proficiencyDistribution} />
      </section>

      <CategoryGrid categories={view.categories} />

      <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <ProjectTimeline items={view.timeline} />
        <SkillsRecommendations items={view.recommendations} />
      </section>

      <RecentActivityList items={view.recentActivity} />
    </main>
  );
}
