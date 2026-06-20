import {
  IntelligenceProfile,
  IntelligenceAssessmentSummaryApi,
  FeatureImportanceItem,
} from './types';

export interface CareerInsightCard {
  career_path: string;
  match_score: number;
  key_factors: string[];
  skill_gaps: string[];
  development_needs?: string[];
}

export interface RecommendationHistoryItem {
  text: string;
  priority: 'high' | 'medium' | 'low';
  date?: string;
}

export interface IntelligenceInsightsView {
  hero: {
    overallScore: number;
    confidence: number;
    careerStage: string;
    totalAssessments: number;
    lastUpdated: string;
  };
  trendPoints: Array<{ date: string; overall: number }>;
  featureImportance: FeatureImportanceItem[];
  strengths: string[];
  improvementAreas: string[];
  careerExplanations: CareerInsightCard[];
  recommendationHistory: RecommendationHistoryItem[];
  assessments: IntelligenceAssessmentSummaryApi[];
}

const fallbackProfile: IntelligenceProfile = {
  user_id: 'placeholder',
  total_assessments: 0,
  current_kash_score: {
    overall: 70,
    knowledge: 68,
    abilities: 72,
    skills: 74,
    experience: 65,
  },
  kash_trend: [
    { date: new Date().toISOString(), overall_score: 70, knowledge_score: 68, abilities_score: 72, skills_score: 74, experience_score: 65 },
  ],
  career_insights: {
    strengths: ['Technical depth', 'Problem solving'],
    improvement_areas: ['Leadership'],
    career_explanations: [
      {
        career: 'software_engineer',
        match_score: 78,
        key_factors: ['Strong skills portfolio'],
        skill_gaps: ['System design'],
        development_needs: ['Lead a cross-team project'],
      },
    ],
  },
  feature_importance_trends: {
    skills_technical_proficiency: {
      current_importance: 0.34,
      trend_direction: 'increasing',
      historical_values: [],
      summary: 'Code quality and repo depth heavily influenced the score.',
    },
  },
  recommendation_history: [
    { recommendation: 'Focus on system design drills', priority: 'high', created_at: new Date().toISOString() },
  ],
  skill_development_progress: {},
  last_assessment: new Date().toISOString(),
  career_stage: 'intermediate',
  confidence: 0.78,
};

const fallbackAssessments: IntelligenceAssessmentSummaryApi[] = [
  {
    assessment_id: 'placeholder',
    assessment_name: 'KASH Intelligence Scan',
    status: 'completed',
    created_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
    overall_score: 70,
    confidence: 0.75,
    career_stage: 'intermediate',
    industry: 'technology',
    career_goals_count: 2,
    strengths_count: 3,
    recommendations_count: 3,
  },
];

function buildFeatureImportance(profile: IntelligenceProfile): FeatureImportanceItem[] {
  const trends = profile.feature_importance_trends ?? {};
  const items = Object.entries(trends).map(([feature, data]: [string, any]) => {
    const currentImportance = data?.current_importance ?? 0;
    const direction = data?.trend_direction === 'decreasing' ? 'negative' : data?.trend_direction === 'stable' ? 'neutral' : 'positive';

    return {
      feature_name: feature.replace(/_/g, ' '),
      feature_value: currentImportance,
      shap_value: currentImportance,
      contribution_percentage: Math.round(currentImportance * 100),
      direction,
      explanation: data?.summary ?? 'Key influence on the overall score.',
    } satisfies FeatureImportanceItem;
  });

  if (items.length === 0) {
    return buildFeatureImportance(fallbackProfile);
  }

  return items.sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value)).slice(0, 6);
}

function buildCareerInsights(profile: IntelligenceProfile): CareerInsightCard[] {
  const insights = profile.career_insights ?? {};
  const explanations = insights.career_explanations ?? [];

  if (!Array.isArray(explanations) || explanations.length === 0) {
    return buildCareerInsights(fallbackProfile);
  }

  return explanations.map((item: any) => ({
    career_path: item.career_path ?? item.career ?? 'unknown',
    match_score: item.match_score ?? 0,
    key_factors: item.key_factors ?? [],
    skill_gaps: item.skill_gaps ?? [],
    development_needs: item.development_needs ?? [],
  }));
}

function buildRecommendationHistory(profile: IntelligenceProfile): RecommendationHistoryItem[] {
  const history = profile.recommendation_history ?? [];

  if (!history.length) {
    return buildRecommendationHistory(fallbackProfile);
  }

  return history.map((entry: any) => ({
    text: entry.recommendation ?? 'Recommendation available',
    priority: (entry.priority ?? 'medium') as RecommendationHistoryItem['priority'],
    date: entry.created_at,
  }));
}

export function buildIntelligenceInsightsView(
  profile?: IntelligenceProfile | null,
  assessments?: IntelligenceAssessmentSummaryApi[] | null
): IntelligenceInsightsView {
  const data = profile ?? fallbackProfile;
  const assessmentSummaries = assessments?.length ? assessments : fallbackAssessments;

  const heroScore = data.current_kash_score?.overall ?? fallbackProfile.current_kash_score!.overall;
  const heroConfidence = data.confidence ?? fallbackProfile.confidence ?? 0;
  const stage = data.career_stage ?? fallbackProfile.career_stage ?? 'explorer';
  const lastUpdated = data.last_assessment ?? fallbackProfile.last_assessment ?? new Date().toISOString();

  const trendPoints = (data.kash_trend ?? []).map((point) => ({
    date: point.date,
    overall: point.overall_score,
  }));

  return {
    hero: {
      overallScore: heroScore,
      confidence: heroConfidence,
      careerStage: stage,
      totalAssessments: data.total_assessments ?? 0,
      lastUpdated,
    },
    trendPoints: trendPoints.length ? trendPoints : fallbackProfile.kash_trend.map((point) => ({ date: point.date, overall: point.overall_score })),
    featureImportance: buildFeatureImportance(data),
    strengths: data.career_insights?.strengths ?? fallbackProfile.career_insights.strengths,
    improvementAreas: data.career_insights?.improvement_areas ?? fallbackProfile.career_insights.improvement_areas,
    careerExplanations: buildCareerInsights(data),
    recommendationHistory: buildRecommendationHistory(data),
    assessments: assessmentSummaries,
  };
}
