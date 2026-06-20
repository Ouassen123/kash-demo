import { KnowledgeProfile, KnowledgeSkillGap } from './types';

export interface KnowledgeDeepDiveView {
  hero: {
    averageScore: number | null;
    totalAssessments: number;
    topSkillCount: number;
    occupationsSuggested: number;
  };
  skillCategories: Array<{ category: string; count: number }>;
  topSkills: string[];
  careerSuggestions: string[];
  skillGaps: KnowledgeSkillGap[];
  learningRecommendations: string[];
  latestAssessment?: KnowledgeProfile['latest_assessment'];
}

const fallbackProfile: KnowledgeProfile = {
  user_id: 'placeholder',
  total_assessments: 0,
  latest_assessment: null,
  average_knowledge_score: null,
  skill_categories: {
    programming: 8,
    data: 5,
    soft_skills: 4,
  },
  top_skills: ['Python', 'Natural Language Processing', 'Team Leadership'],
  career_suggestions: ['Data Scientist', 'AI Engineer'],
  skill_gaps: [
    {
      occupation: 'Data Scientist',
      missing_skills: ['Spark', 'Model Monitoring'],
      skill_coverage: 0.72,
      priority: 'high',
    },
  ],
  learning_recommendations: ['Complete Spark fundamentals course', 'Implement a model monitoring pipeline'],
};

export function buildKnowledgeDeepDiveView(profile?: KnowledgeProfile | null): KnowledgeDeepDiveView {
  const data = profile ?? fallbackProfile;
  const categories = Object.entries(data.skill_categories ?? {}).map(([category, count]) => ({ category, count }));

  const occupationsSuggested = data.latest_assessment?.occupations_suggested ?? data.career_suggestions?.length ?? 0;

  return {
    hero: {
      averageScore: data.average_knowledge_score,
      totalAssessments: data.total_assessments,
      topSkillCount: data.top_skills?.length ?? 0,
      occupationsSuggested,
    },
    skillCategories: categories.length
      ? categories
      : Object.entries(fallbackProfile.skill_categories).map(([category, count]) => ({ category, count })),
    topSkills: data.top_skills?.length ? data.top_skills : fallbackProfile.top_skills,
    careerSuggestions: data.career_suggestions?.length ? data.career_suggestions : fallbackProfile.career_suggestions,
    skillGaps: data.skill_gaps?.length ? data.skill_gaps : fallbackProfile.skill_gaps,
    learningRecommendations: data.learning_recommendations?.length
      ? data.learning_recommendations
      : fallbackProfile.learning_recommendations,
    latestAssessment: data.latest_assessment ?? fallbackProfile.latest_assessment,
  };
}
