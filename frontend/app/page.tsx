'use client';

import Link from 'next/link';
import { useEffect, useState, Suspense } from 'react';
import dynamic from 'next/dynamic';
import { fetchDashboardData } from '@/lib/api';
import { buildDashboardViewModel } from '@/lib/dashboard';
import type { DashboardViewModel } from '@/lib/types';
import { OverallScoreHero } from '@/components/dashboard/overall-score-hero';
import { DomainScoreCard } from '@/components/dashboard/domain-score-card';
import { InsightsPanel } from '@/components/dashboard/insights-panel';
import { RecommendationsPanel } from '@/components/dashboard/recommendations-panel';
import { AssessmentActivityTimeline } from '@/components/dashboard/assessment-activity';
import { SkillsHighlightsPanel } from '@/components/dashboard/skills-highlights';

const TrendChart = dynamic(
  () => import('@/components/dashboard/trend-chart'),
  { ssr: false, loading: () => <div className="glass-panel h-72 animate-pulse" /> }
);

function Skeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="glass-panel p-5 animate-pulse">
          <div className="h-4 bg-white/10 rounded w-24 mb-4" />
          <div className="h-10 bg-white/10 rounded w-20" />
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [viewModel, setViewModel] = useState<DashboardViewModel>(buildDashboardViewModel());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData()
      .then((data) => setViewModel(buildDashboardViewModel(data)))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 lg:px-0">
      <Skeleton />
    </main>
  );

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 lg:px-0">
      <div className="flex items-center justify-between rounded-2xl border border-indigo-400/30 bg-indigo-500/10 px-6 py-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-indigo-300/70">KASH Assessment</p>
          <p className="text-lg font-semibold text-white mt-0.5">Passer les 4 tests KASH</p>
          <p className="text-sm text-white/60 mt-1">Abilities → Knowledge → Entretien → Skills</p>
        </div>
        <Link
          href="/kash/start"
          className="inline-flex items-center gap-2 rounded-full bg-indigo-500 text-white px-6 py-2.5 text-sm font-semibold hover:bg-indigo-400 transition shadow-lg"
        >
          Démarrer KASH
          <span aria-hidden>→</span>
        </Link>
      </div>

      <OverallScoreHero
        overallScore={viewModel.overallScore}
        confidence={viewModel.confidence}
        careerStage={viewModel.careerStage}
        stageTagline={viewModel.stageTagline}
        lastUpdated={viewModel.lastUpdated}
      />

      <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <TrendChart points={viewModel.trendPoints} />
        <div className="space-y-4">
          <Suspense fallback={<Skeleton />}>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-1">
              {viewModel.domainScores.map((domain) => (
                <DomainScoreCard key={domain.key} domain={domain} />
              ))}
            </div>
          </Suspense>
          <RecommendationsPanel items={viewModel.recommendations} />
        </div>

        <div className="glass-panel flex flex-col gap-4 p-6 text-white/80">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Intelligence Insights</p>
            <p className="text-2xl font-semibold mt-1 text-white">Explainability & path planning</p>
            <p className="text-sm text-white/70 mt-2 max-w-2xl">
              Explore KASH trendlines, SHAP feature importance, career alignment, and recommendation history with links to
              detailed assessments.
            </p>
          </div>
          <div>
            <Link
              href="/intelligence/insights"
              className="inline-flex items-center gap-2 rounded-full bg-white text-midnight px-6 py-2 text-sm font-semibold hover:bg-mist transition"
            >
              View Intelligence Insights
              <span aria-hidden>→</span>
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <InsightsPanel insights={viewModel.insights} />
        <AssessmentActivityTimeline items={viewModel.assessmentActivity} />
      </section>

      <SkillsHighlightsPanel
        languages={viewModel.skillsHighlights.languages}
        topSkills={viewModel.skillsHighlights.topSkills}
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="glass-panel flex flex-col gap-4 p-6 text-white/80">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-mist/70">KASH Journey</p>
            <p className="text-2xl font-semibold mt-1 text-white">Pass all 4 tests</p>
            <p className="text-sm text-white/70 mt-2 max-w-2xl">
              Complete Abilities, CV Knowledge upload, webcam interview questions, and Skills code upload before reviewing
              your global result.
            </p>
          </div>
          <div>
            <Link
              href="/kash/start"
              className="inline-flex items-center gap-2 rounded-full bg-white text-midnight px-6 py-2 text-sm font-semibold hover:bg-mist transition"
            >
              Start KASH Journey
              <span aria-hidden>→</span>
            </Link>
          </div>
        </div>

        <div className="glass-panel flex flex-col gap-4 p-6 text-white/80">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Skills Deep Dive</p>
            <p className="text-2xl font-semibold mt-1 text-white">Explore technical intelligence</p>
            <p className="text-sm text-white/70 mt-2 max-w-2xl">
              Inspect language distribution, proficiency clusters, project timelines, and personalized recommendations in a
              dedicated workspace.
            </p>
          </div>
          <div>
            <Link
              href="/skills/deep-dive"
              className="inline-flex items-center gap-2 rounded-full bg-white text-midnight px-6 py-2 text-sm font-semibold hover:bg-mist transition"
            >
              View Skills Deep Dive
              <span aria-hidden>→</span>
            </Link>
          </div>
        </div>

        <div className="glass-panel flex flex-col gap-4 p-6 text-white/80">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Knowledge Deep Dive</p>
            <p className="text-2xl font-semibold mt-1 text-white">Understand CV + taxonomy signals</p>
            <p className="text-sm text-white/70 mt-2 max-w-2xl">
              Review normalized CV attributes, ESCO skill mappings, career suggestions, and learning plans grounded in
              occupation coverage.
            </p>
          </div>
          <div>
            <Link
              href="/knowledge/deep-dive"
              className="inline-flex items-center gap-2 rounded-full bg-white text-midnight px-6 py-2 text-sm font-semibold hover:bg-mist transition"
            >
              View Knowledge Deep Dive
              <span aria-hidden>→</span>
            </Link>
          </div>
        </div>

        <div className="glass-panel flex flex-col gap-4 p-6 text-white/80">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Abilities Deep Dive</p>
            <p className="text-2xl font-semibold mt-1 text-white">Drill into adaptive assessments</p>
            <p className="text-sm text-white/70 mt-2 max-w-2xl">
              Inspect cognitive domain performance, improvement trends, personalized recommendations, and recent quiz
              sessions.
            </p>
          </div>
          <div>
            <Link
              href="/abilities/deep-dive"
              className="inline-flex items-center gap-2 rounded-full bg-white text-midnight px-6 py-2 text-sm font-semibold hover:bg-mist transition"
            >
              View Abilities Deep Dive
              <span aria-hidden>→</span>
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
