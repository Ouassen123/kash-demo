'use client';

import { BarChart3, Brain, ShieldAlert, Sparkles, Target } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import type { HabitsEmotionMetric, HabitsInterviewAnalysisResponse } from '@/lib/types';

interface HabitsResultsViewProps {
  analysis: HabitsInterviewAnalysisResponse;
  className?: string;
}

const metricCards = [
  { key: 'clarity_score', label: 'Clarté', accent: 'from-cyan-400 to-sky-500' },
  { key: 'relevance_score', label: 'Pertinence', accent: 'from-violet-400 to-fuchsia-500' },
  { key: 'engagement_score', label: 'Engagement', accent: 'from-amber-300 to-orange-500' },
  { key: 'confidence_score', label: 'Confiance', accent: 'from-emerald-400 to-teal-500' },
] as const;

const emotionPalette: Record<string, string> = {
  happy: '#34d399',
  joy: '#34d399',
  neutral: '#60a5fa',
  surprise: '#a78bfa',
  fear: '#f59e0b',
  sad: '#ef4444',
  angry: '#f97316',
  disgust: '#fb7185',
};

function getMetricTone(score: number): string {
  if (score >= 80) return 'text-emerald-300';
  if (score >= 60) return 'text-cyan-300';
  if (score >= 40) return 'text-amber-300';
  return 'text-rose-300';
}

function Gauge({ label, value, accent, animate }: { label: string; value: number; accent: string; animate: boolean }) {
  const percent = Math.max(0, Math.min(100, value));
  const colorClass = getMetricTone(percent);
  const animatedPercent = animate ? percent : 0;
  const ringTone = percent >= 80 ? '#34d399' : percent >= 60 ? '#60a5fa' : percent >= 40 ? '#f59e0b' : '#fb7185';

  return (
    <article className="rounded-[28px] border border-slate-200/80 bg-white/70 p-5 shadow-lg shadow-indigo-500/5 backdrop-blur-md transition-all duration-700 ease-out dark:border-slate-800 dark:bg-slate-900/40">
      <div className="flex items-center justify-between gap-4">
        <div className="space-y-2">
          <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500 dark:text-slate-400">{label}</p>
          <p className={`text-3xl font-semibold tracking-tight ${colorClass}`}>{Math.round(percent)}%</p>
        </div>
        <div
          className="relative h-18 w-18 rounded-full p-1 shadow-lg shadow-indigo-500/5 transition-all duration-1000 ease-out"
          style={{ background: `conic-gradient(from 180deg, ${ringTone} ${animatedPercent}%, rgba(148,163,184,0.14) 0)` }}
          aria-hidden="true"
        >
          <div className="flex h-full w-full items-center justify-center rounded-full bg-white/90 dark:bg-slate-950/90">
            <div className={`h-8 w-8 rounded-full bg-gradient-to-br ${accent} opacity-90`} />
          </div>
        </div>
      </div>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-200/80 dark:bg-slate-800">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${accent} shadow-lg shadow-indigo-500/5 transition-all duration-1000 ease-out`}
          style={{ width: `${animatedPercent}%` }}
        />
      </div>
    </article>
  );
}

function EmotionRadar({ emotions, animate }: { emotions: HabitsEmotionMetric[]; animate: boolean }) {
  const normalized = useMemo(() => {
    const entries = emotions
      .map((emotion) => ({
        key: emotion.emotion.toLowerCase(),
        label: emotion.emotion,
        value: Math.max(0, emotion.confidence),
      }))
      .filter((item) => item.value > 0)
      .sort((a, b) => b.value - a.value);

    const total = entries.reduce((sum, entry) => sum + entry.value, 0) || 1;
    return entries.map((entry) => ({ ...entry, percent: (entry.value / total) * 100 }));
  }, [emotions]);

  const conic = normalized.length
    ? normalized
        .map((entry, index) => {
          const start = normalized.slice(0, index).reduce((sum, item) => sum + item.percent, 0);
          const end = start + entry.percent;
          const color = emotionPalette[entry.key] ?? ['#34d399', '#60a5fa', '#a78bfa', '#f59e0b', '#ef4444'][index % 5];
          return `${color} ${start}% ${end}%`;
        })
        .join(', ')
    : '#60a5fa 0% 100%';

  return (
    <section className="rounded-[32px] border border-slate-200/80 bg-white/70 p-6 shadow-lg shadow-indigo-500/5 backdrop-blur-md transition-all duration-700 ease-out dark:border-slate-800 dark:bg-slate-900/40">
      <div className="flex items-center gap-2">
        <Brain className="h-4 w-4 text-cyan-500 dark:text-cyan-300" />
        <p className="text-sm font-semibold text-slate-900 dark:text-white">Radar émotionnel</p>
      </div>
      <div className="mt-5 grid gap-5 md:grid-cols-[220px,1fr] md:items-center">
        <div
          className={`mx-auto flex h-44 w-44 items-center justify-center rounded-full p-3 shadow-2xl shadow-indigo-500/10 transition-all duration-1000 ease-out ${animate ? 'scale-100 opacity-100' : 'scale-95 opacity-70'}`}
          style={{ background: `conic-gradient(${conic})` }}
        >
          <div className="flex h-full w-full flex-col items-center justify-center rounded-full border border-slate-200/80 bg-white/95 text-center dark:border-slate-800 dark:bg-slate-950/90">
            <p className="text-[11px] uppercase tracking-[0.35em] text-slate-500 dark:text-slate-400">Distribution</p>
            <p className="mt-1 text-3xl font-semibold text-slate-900 dark:text-white">{normalized.length}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">émotions détectées</p>
          </div>
        </div>

        <div className="grid gap-2 sm:grid-cols-2">
          {normalized.length > 0 ? (
            normalized.map((emotion) => (
              <div
                key={emotion.key}
                className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200/80 bg-white/80 px-3 py-3 shadow-lg shadow-indigo-500/5 backdrop-blur-md transition-all duration-700 ease-out dark:border-slate-800 dark:bg-slate-950/50"
              >
                <div className="flex items-center gap-2.5">
                  <span
                    className="h-2.5 w-2.5 rounded-full shadow-sm"
                    style={{ backgroundColor: emotionPalette[emotion.key] ?? '#60a5fa' }}
                  />
                  <span className="text-sm font-medium text-slate-800 dark:text-slate-100">{emotion.label}</span>
                </div>
                <span className="text-sm text-slate-500 dark:text-slate-400">{Math.round(emotion.percent)}%</span>
              </div>
            ))
          ) : (
            <div className="rounded-2xl border border-slate-200/80 bg-white/80 px-3 py-4 text-sm text-slate-500 shadow-lg shadow-indigo-500/5 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-400">
              Aucune émotion détectée.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export function HabitsResultsView({ analysis, className }: HabitsResultsViewProps) {
  const [animate, setAnimate] = useState(false);
  const strengths = analysis.strengths?.length ? analysis.strengths : ['Réponses structurées et complètes'];
  const improvementAreas = analysis.improvement_areas?.length
    ? analysis.improvement_areas
    : ['Continuer à affiner la précision et la profondeur des réponses'];

  useEffect(() => {
    const timer = window.setTimeout(() => setAnimate(true), 120);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <section
      className={`relative overflow-hidden rounded-[36px] border border-slate-200/80 bg-white/70 p-6 shadow-2xl shadow-indigo-500/5 backdrop-blur-md transition-all duration-700 ease-out dark:border-slate-800 dark:bg-slate-900/40 ${className ?? ''}`}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-48 bg-gradient-to-b from-indigo-500/10 via-transparent to-transparent" />

      <div className="relative flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
        <div className="space-y-3">
          <p className="text-[11px] uppercase tracking-[0.45em] text-slate-500 dark:text-slate-400">Habits insights</p>
          <h2 className="text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">Analyse multimodale de l’entretien</h2>
          <p className="max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
            Synthèse premium des dimensions textuelles, vocales et faciales pour visualiser rapidement la qualité de l’entretien et les signaux comportementaux.
          </p>
        </div>

        <div className="rounded-[28px] border border-slate-200/80 bg-white/85 px-6 py-5 text-right shadow-lg shadow-indigo-500/5 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/50">
          <p className="text-[11px] uppercase tracking-[0.35em] text-slate-500 dark:text-slate-400">Score composite</p>
          <p className={`mt-2 text-5xl font-semibold tracking-tight ${getMetricTone(analysis.composite_score)}`}>
            {Math.round(analysis.composite_score)}
            <span className="ml-1 text-lg text-slate-500 dark:text-slate-400">/100</span>
          </p>
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Temps de traitement : {Math.round(analysis.processing_time_ms)} ms</p>
        </div>
      </div>

      <div className="relative mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metricCards.map((card) => (
          <Gauge
            key={card.key}
            label={card.label}
            value={analysis[card.key]}
            accent={card.accent}
            animate={animate}
          />
        ))}
      </div>

      <div className="relative mt-6 grid gap-6 xl:grid-cols-[1.25fr,0.75fr]">
        <EmotionRadar emotions={analysis.emotions_detected ?? []} animate={animate} />

        <section className="rounded-[32px] border border-slate-200/80 bg-white/70 p-6 shadow-lg shadow-indigo-500/5 backdrop-blur-md transition-all duration-700 ease-out dark:border-slate-800 dark:bg-slate-900/40">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-emerald-500 dark:text-emerald-300" />
            <p className="text-sm font-semibold text-slate-900 dark:text-white">Profil comportemental</p>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {[
              { label: 'Style de communication', value: analysis.behavioral_profile.communication_style, icon: BarChart3 },
              { label: 'Niveau de motivation', value: analysis.behavioral_profile.motivation_level, icon: Sparkles },
              { label: 'Indicateur de stress', value: analysis.behavioral_profile.stress_indicators, icon: ShieldAlert },
              { label: 'Recommandation', value: analysis.behavioral_profile.overall_recommendation, icon: Brain },
            ].map((item) => (
              <article key={item.label} className="rounded-2xl border border-slate-200/80 bg-white/85 p-4 shadow-lg shadow-indigo-500/5 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/45">
                <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                  <item.icon className="h-4 w-4 text-cyan-500 dark:text-cyan-300" />
                  <p className="text-[11px] uppercase tracking-[0.3em]">{item.label}</p>
                </div>
                <p className="mt-3 text-lg font-semibold capitalize text-slate-950 dark:text-white">{item.value.replaceAll('_', ' ')}</p>
              </article>
            ))}
          </div>
        </section>
      </div>

      <div className="relative mt-6 grid gap-4 xl:grid-cols-[0.95fr,1.05fr]">
        <section className="rounded-[30px] border border-emerald-200/70 bg-emerald-500/10 p-5 shadow-lg shadow-emerald-500/5 backdrop-blur-md dark:border-emerald-900/40 dark:bg-emerald-500/8">
          <p className="text-[11px] uppercase tracking-[0.35em] text-emerald-700/80 dark:text-emerald-200/70">Points forts</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {strengths.map((strength) => (
              <span
                key={strength}
                className="rounded-full border border-emerald-300/25 bg-white/80 px-3 py-1.5 text-sm text-emerald-700 shadow-sm shadow-emerald-500/5 dark:bg-slate-950/45 dark:text-emerald-200"
              >
                {strength}
              </span>
            ))}
          </div>
        </section>

        <section className="rounded-[30px] border border-amber-200/70 bg-amber-500/10 p-5 shadow-lg shadow-amber-500/5 backdrop-blur-md dark:border-amber-900/40 dark:bg-amber-500/8">
          <p className="text-[11px] uppercase tracking-[0.35em] text-amber-700/80 dark:text-amber-200/70">Axes d’amélioration</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {improvementAreas.map((area) => (
              <span
                key={area}
                className="rounded-full border border-amber-300/25 bg-white/80 px-3 py-1.5 text-sm text-amber-700 shadow-sm shadow-amber-500/5 dark:bg-slate-950/45 dark:text-amber-200"
              >
                {area}
              </span>
            ))}
          </div>
        </section>
      </div>
    </section>
  );
}
