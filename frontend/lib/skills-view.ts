import { SkillsProfile } from './types';

export interface SkillsDeepDiveView {
  hero: {
    averageScore: number;
    bestScore: number;
    improvementTrend: string;
    totalAssessments: number;
    totalUniqueSkills: number;
    languageDiversity: number;
  };
  languages: Array<{ name: string; percentage: number; count: number }>;
  proficiencyDistribution: Array<{ level: string; count: number }>;
  categories: Array<{ name: string; skills: Array<{ name: string; confidence: number; proficiency_level: string }> }>;
  timeline: Array<{ date: string; complexity: number; project_name: string }>;
  recommendations: string[];
  recentActivity: SkillsProfile['recent_activity'];
}

const fallbackProfile: SkillsProfile = {
  user_id: 'placeholder',
  total_assessments: 0,
  technical_skills: {
    skills_by_category: {
      programming: [
        { name: 'Python', confidence: 0.85, proficiency_level: 'advanced' },
        { name: 'TypeScript', confidence: 0.72, proficiency_level: 'intermediate' },
      ],
    },
    proficiency_distribution: { beginner: 1, intermediate: 2, advanced: 1, expert: 0 },
    total_unique_skills: 4,
    top_skills: [
      { name: 'Python', confidence: 0.85 },
      { name: 'TypeScript', confidence: 0.72 },
    ],
  },
  programming_languages: {
    Python: 1200,
    TypeScript: 800,
    Go: 200,
  },
  overall_performance: {
    average_score: 68,
    best_score: 82,
    improvement_trend: 'improving',
    skill_diversity: 4,
    language_diversity: 3,
  },
  project_complexity_trend: [],
  recommendations: ['Ship a TypeScript-heavy project', 'Practice Go concurrency patterns'],
  recent_activity: [],
  last_assessment: undefined,
};

export function buildSkillsDeepDiveView(profile?: SkillsProfile | null): SkillsDeepDiveView {
  const data = profile ?? fallbackProfile;
  const performance = data.overall_performance ?? {};
  const technicalSkills = data.technical_skills ?? {};
  const languages = data.programming_languages ?? {};

  const totalLanguageLines = Object.values(languages).reduce((acc, value) => acc + value, 0) || 1;
  const languageList = Object.entries(languages)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 6)
    .map(([name, count]) => ({
      name,
      count,
      percentage: Math.round((count / totalLanguageLines) * 100),
    }));

  const proficiencyDistribution = Object.entries(technicalSkills.proficiency_distribution ?? {}).map(([level, count]) => ({
    level,
    count: Number(count) || 0,
  }));

  const categories = Object.entries(technicalSkills.skills_by_category ?? {}).map(([name, skills]) => ({
    name,
    skills: skills.slice(0, 5),
  }));

  const timeline = (data.project_complexity_trend ?? []).slice(0, 6);

  return {
    hero: {
      averageScore: performance.average_score ?? 0,
      bestScore: performance.best_score ?? 0,
      improvementTrend: performance.improvement_trend ?? 'insufficient_data',
      totalAssessments: data.total_assessments ?? 0,
      totalUniqueSkills: technicalSkills.total_unique_skills ?? performance.skill_diversity ?? 0,
      languageDiversity: performance.language_diversity ?? languageList.length,
    },
    languages: languageList.length ? languageList : [
      { name: 'Python', count: 1200, percentage: 45 },
      { name: 'TypeScript', count: 800, percentage: 30 },
      { name: 'Go', count: 200, percentage: 15 },
      { name: 'Rust', count: 150, percentage: 10 },
    ],
    proficiencyDistribution:
      proficiencyDistribution.length > 0
        ? proficiencyDistribution
        : [
            { level: 'beginner', count: 2 },
            { level: 'intermediate', count: 3 },
            { level: 'advanced', count: 2 },
            { level: 'expert', count: 1 },
          ],
    categories: categories.length ? categories : [{ name: 'programming', skills: technicalSkills.skills_by_category?.programming ?? [] }],
    timeline: timeline.length
      ? timeline
      : [
          { date: new Date().toISOString(), complexity: 65, project_name: 'Sample Project' },
          { date: new Date(Date.now() - 6048e5).toISOString(), complexity: 55, project_name: 'API Refactor' },
        ],
    recommendations: data.recommendations?.length ? data.recommendations : fallbackProfile.recommendations,
    recentActivity: data.recent_activity?.length ? data.recent_activity : fallbackProfile.recent_activity,
  };
}
