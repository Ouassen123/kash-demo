import {
  DashboardViewModel,
  DomainScore,
  IntelligenceProfile,
  IntelligenceAssessmentSummaryApi,
  SkillsProfile,
  Insight,
  RecommendationItem,
  AssessmentActivity,
} from './types';

const domainLabels: Record<string, string> = {
  knowledge: 'Knowledge',
  abilities: 'Abilities',
  skills: 'Skills',
  experience: 'Experience',
};

export const stageTaglines: Record<string, string> = {
  explorer: 'Building awareness and mapping possibilities.',
  beginner: 'Foundational capabilities formed—keep experimenting.',
  intermediate: 'Skills compounding—double down on strengths.',
  advanced: 'Leadership readiness emerging—refine your craft.',
  expert: 'Driving innovation and mentoring others.',
};

const skeletonProfile: IntelligenceProfile = {
  user_id: 'placeholder-user',
  total_assessments: 0,
  current_kash_score: {
    overall: 0,
    knowledge: 0,
    abilities: 0,
    skills: 0,
    experience: 0,
  },
  kash_trend: [],
  career_insights: {},
  feature_importance_trends: {},
  recommendation_history: [],
  skill_development_progress: {},
  career_stage: 'explorer',
  confidence: 0.2,
};

const sampleAssessments: IntelligenceAssessmentSummaryApi[] = [
  {
    assessment_id: 'sample-1',
    assessment_name: 'Holistic Intelligence Scan',
    status: 'completed',
    created_at: new Date().toISOString(),
    overall_score: 68,
    confidence: 0.74,
    career_stage: 'intermediate',
    industry: 'technology',
    career_goals_count: 2,
    strengths_count: 3,
    recommendations_count: 4,
  },
];

const sampleSkills: SkillsProfile = {
  user_id: 'placeholder-user',
  total_assessments: 0,
  technical_skills: {
    skills_by_category: {
      programming: [
        { name: 'Python', confidence: 0.82, proficiency_level: 'advanced' },
        { name: 'TypeScript', confidence: 0.74, proficiency_level: 'intermediate' },
      ],
    },
    proficiency_distribution: {
      beginner: 2,
      intermediate: 4,
      advanced: 3,
      expert: 1,
    },
    total_unique_skills: 6,
    top_skills: [
      { name: 'Python', confidence: 0.82 },
      { name: 'TypeScript', confidence: 0.74 },
    ],
  },
  programming_languages: {
    Python: 24,
    TypeScript: 14,
    Go: 6,
  },
  overall_performance: {
    average_score: 68,
    best_score: 82,
    improvement_trend: 'improving',
    skill_diversity: 6,
    language_diversity: 3,
  },
  project_complexity_trend: [],
  recommendations: [
    'Deepen TypeScript architecture patterns.',
    'Explore distributed systems design.',
  ],
  recent_activity: [],
};

function buildDomainScores(profile: IntelligenceProfile): DomainScore[] {
  const current = profile.current_kash_score ?? {
    overall: 0,
    knowledge: 0,
    abilities: 0,
    skills: 0,
    experience: 0,
  };

  const trendLookup = new Map<string, number>();
  const trendPairs = profile.kash_trend.slice(0, 6);
  if (trendPairs.length >= 2) {
    const latest = trendPairs[0];
    const previous = trendPairs[1];
    trendLookup.set('knowledge', latest.knowledge_score - previous.knowledge_score);
    trendLookup.set('abilities', latest.abilities_score - previous.abilities_score);
    trendLookup.set('skills', latest.skills_score - previous.skills_score);
    trendLookup.set('experience', latest.experience_score - previous.experience_score);
  }

  const confidence = profile.confidence ?? 0.5;

  return (['knowledge', 'abilities', 'skills', 'experience'] as const).map((key) => ({
    key,
    label: domainLabels[key],
    score: current[key],
    confidence,
    trend: trendLookup.get(key) ?? 0,
  }));
}

function deriveInsights(profile: IntelligenceProfile): Insight[] {
  const insights: Insight[] = [];
  const careerInsights = profile.career_insights ?? {};

  Object.entries(careerInsights).forEach(([title, payload]) => {
    if (!payload) return;
    insights.push({
      title,
      description: typeof payload === 'string' ? payload : payload.summary ?? 'Insight available',
      priority: payload.priority ?? 'medium',
      supportingData: payload,
    });
  });

  if (insights.length === 0) {
    insights.push({
      title: 'Intelligence assessments pending',
      description: 'Run your first intelligence assessment to unlock personalized insights.',
      priority: 'medium',
    });
  }

  return insights.slice(0, 4);
}

function deriveRecommendations(profile: IntelligenceProfile, skills?: SkillsProfile | null): RecommendationItem[] {
  const items: RecommendationItem[] = [];

  profile.recommendation_history?.forEach((rec) => {
    if (!rec) return;
    const texts: string[] = Array.isArray(rec.recommendations)
      ? rec.recommendations
      : rec.recommendation
      ? [rec.recommendation]
      : [];
    texts.forEach((text: string) => {
      items.push({
        text,
        source: 'Intelligence',
        priority: (rec.priority ?? 'medium') as RecommendationItem['priority'],
      });
    });
  });

  skills?.recommendations?.forEach((rec) => {
    items.push({ text: rec, source: 'Skills', priority: 'medium' });
  });

  if (items.length === 0) {
    items.push({
      text: 'Complete the KASH assessment to receive tailored guidance.',
      source: 'System',
      priority: 'high',
    });
  }

  return items.slice(0, 5);
}

function buildAssessmentActivity(assessments: IntelligenceAssessmentSummaryApi[] = []): AssessmentActivity[] {
  if (assessments.length === 0) {
    return [
      {
        id: 'sample-activity',
        module: 'intelligence',
        title: 'Awaiting first intelligence assessment',
        date: new Date().toISOString(),
        score: 0,
        status: 'in_progress',
      },
    ];
  }

  return assessments.map((assessment) => ({
    id: assessment.assessment_id,
    module: 'intelligence',
    title: assessment.assessment_name,
    date: assessment.created_at,
    score: assessment.overall_score ?? 0,
    status: assessment.status as AssessmentActivity['status'],
  }));
}

function buildSkillsHighlight(skills?: SkillsProfile | null) {
  const languages = skills?.programming_languages ?? {};
  const totalLines = Object.values(languages).reduce((acc, val) => acc + val, 0) || 1;

  const languageList = Object.entries(languages)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 4)
    .map(([name, count]) => ({
      name,
      percentage: Math.round((count / totalLines) * 100),
    }));

  const topSkills = skills?.technical_skills?.top_skills ?? [];

  return {
    languages: languageList.length ? languageList : [
      { name: 'Python', percentage: 45 },
      { name: 'TypeScript', percentage: 35 },
      { name: 'Go', percentage: 20 },
    ],
    topSkills: topSkills.length ? topSkills : [
      { name: 'Problem Solving', confidence: 0.78 },
      { name: 'Systems Design', confidence: 0.71 },
    ],
  };
}

export function buildDashboardViewModel(data?: {
  intelligenceProfile?: IntelligenceProfile | null;
  intelligenceAssessments?: IntelligenceAssessmentSummaryApi[] | null;
  skillsProfile?: SkillsProfile | null;
}): DashboardViewModel {
  const profile = data?.intelligenceProfile ?? skeletonProfile;
  const assessments = data?.intelligenceAssessments ?? sampleAssessments;
  const skills = data?.skillsProfile ?? sampleSkills;

  const domainScores = buildDomainScores(profile);
  const trendPoints = (profile.kash_trend ?? []).slice(0, 8).reverse().map((point) => ({
    date: point.date,
    overall: point.overall_score,
  }));

  if (trendPoints.length === 0 && profile.current_kash_score) {
    trendPoints.push({ date: new Date().toISOString(), overall: profile.current_kash_score.overall });
  }

  const insights = deriveInsights(profile);
  const recommendations = deriveRecommendations(profile, skills);
  const assessmentActivity = buildAssessmentActivity(assessments);
  const lastUpdated = profile.last_assessment ?? assessmentActivity[0]?.date ?? new Date().toISOString();
  const stage = profile.career_stage ?? 'explorer';

  return {
    lastUpdated,
    overallScore: profile.current_kash_score?.overall ?? 0,
    confidence: profile.confidence ?? 0,
    careerStage: stage,
    stageTagline: stageTaglines[stage] ?? stageTaglines.explorer,
    domainScores,
    trendPoints,
    insights,
    recommendations,
    assessmentActivity,
    skillsHighlights: buildSkillsHighlight(skills),
  };
}
