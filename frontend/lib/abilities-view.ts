import { AbilitiesProfile } from './types';

export interface AbilitiesDeepDiveView {
  hero: {
    averageScore: number;
    bestScore: number;
    totalAssessments: number;
    improvementTrend: string;
  };
  domainScores: Array<{ domain: string; score: number }>;
  recommendations: string[];
  recentActivity: AbilitiesProfile['recent_activity'];
}

const fallbackProfile: AbilitiesProfile = {
  user_id: 'placeholder',
  total_assessments: 0,
  domain_scores: {
    analytical_reasoning: 72,
    verbal_reasoning: 65,
    problem_solving: 78,
    creativity: 69,
  },
  overall_performance: {
    average_score: 71,
    best_score: 82,
    total_assessments: 4,
    improvement_trend: 'improving',
  },
  recommendations: [
    'Continue practicing analytical reasoning through timed case drills.',
    'Run another adaptive assessment for verbal reasoning next week.',
  ],
  recent_activity: [],
  last_assessment: undefined,
};

export function buildAbilitiesDeepDiveView(profile?: AbilitiesProfile | null): AbilitiesDeepDiveView {
  const data = profile ?? fallbackProfile;
  const overall = data.overall_performance ?? {};

  const rawDomainScores = data.domain_scores ?? {};
  const domainScores = Object.entries(rawDomainScores).map(([domain, score]) => ({
    domain,
    // score may be a nested dict like {score: 20, correct: 1, ...} or a plain number
    score: typeof score === 'object' && score !== null ? (score as Record<string, number>).score ?? 0 : (score as number),
  }));

  return {
    hero: {
      averageScore: overall.average_score ?? 0,
      bestScore: overall.best_score ?? 0,
      totalAssessments: data.total_assessments ?? overall.total_assessments ?? 0,
      improvementTrend: overall.improvement_trend ?? 'insufficient_data',
    },
    domainScores: domainScores.length
      ? domainScores
      : Object.entries(fallbackProfile.domain_scores).map(([domain, score]) => ({ domain, score })),
    recommendations: data.recommendations?.length ? data.recommendations : fallbackProfile.recommendations,
    recentActivity: data.recent_activity?.length ? data.recent_activity : fallbackProfile.recent_activity,
  };
}
