export type DomainKey = 'knowledge' | 'abilities' | 'skills' | 'experience';

export interface DomainScore {
  key: DomainKey;
  label: string;
  score: number;
  confidence: number;
  trend: number; // delta vs previous assessment
}

export interface KnowledgeSkillGap {
  occupation: string;
  missing_skills: string[];
  skill_coverage: number;
  priority: 'high' | 'medium' | 'low';
}

export interface KnowledgeAssessmentSummary {
  assessment_id: string;
  assessment_name: string;
  status: string;
  normalized_score: number | null;
  confidence_score: number | null;
  created_at: string;
  completed_at?: string | null;
  total_skills_found: number;
  occupations_suggested: number;
  experience_years: number;
}

export interface KnowledgeProfile {
  user_id: string;
  total_assessments: number;
  latest_assessment: KnowledgeAssessmentSummary | null;
  average_knowledge_score: number | null;
  skill_categories: Record<string, number>;
  top_skills: string[];
  career_suggestions: string[];
  skill_gaps: KnowledgeSkillGap[];
  learning_recommendations: string[];
}

export interface AbilitiesRecentActivityItem {
  assessment_id: string;
  domain: string;
  score: number;
  completed_at?: string | null;
}

export interface AbilitiesOverallPerformance {
  average_score?: number;
  best_score?: number;
  total_assessments?: number;
  improvement_trend?: string;
}

export interface AbilitiesProfile {
  user_id: string;
  total_assessments: number;
  domain_scores: Record<string, number>;
  overall_performance: AbilitiesOverallPerformance;
  recommendations: string[];
  recent_activity: AbilitiesRecentActivityItem[];
  last_assessment?: string | null;
}

export interface AbilitiesAssessmentQuestion {
  id: string;
  type: string;
  domain: string;
  difficulty: string;
  question_text: string;
  options: string[];
  time_limit_seconds: number;
  points_possible: number;
}

export interface StartAbilitiesAssessmentPayload {
  quiz_type: 'cognitive' | 'behavioral' | 'technical';
  domain:
    | 'memory'
    | 'attention'
    | 'processing_speed'
    | 'executive_function'
    | 'language'
    | 'visual_spatial'
    | 'problem_solving'
    | 'creativity';
  num_questions: number;
  adaptive: boolean;
}

export interface StartAbilitiesAssessmentResponse {
  assessment_id: string;
  session_id: string;
  quiz_type: string;
  domain: string;
  total_questions: number;
  adaptive: boolean;
  current_question: AbilitiesAssessmentQuestion | null;
  question_number: number;
  time_limit_seconds: number;
}

export interface SubmitAbilitiesAnswerPayload {
  session_id: string;
  question_id: string;
  answer: string | number | string[];
  response_time_ms: number;
}

export interface SubmitAbilitiesAnswerResponse {
  is_correct: boolean;
  question_number: number;
  total_questions: number;
  progress: number;
  quiz_completed: boolean;
  next_question: AbilitiesAssessmentQuestion | null;
  time_limit_seconds?: number;
  results?: {
    percentage?: number;
    correct_answers?: number;
    total_questions?: number;
    time_spent_seconds?: number;
    recommendations?: string[];
  };
}

export interface HabitsInterviewAnswer {
  question_id: string;
  question_text: string;
  answer_text: string;
}

export interface HabitsInterviewRequest {
  answers: HabitsInterviewAnswer[];
  audio_base64?: string | null;
  video_frames_base64?: string[] | null;
  industry?: string | null;
}

export interface HabitsVoiceMetrics {
  speech_rate: number;
  volume_db: number;
  pitch_variation: number;
  pause_ratio: number;
  fluency_score: number;
}

export interface HabitsEmotionMetric {
  emotion: string;
  confidence: number;
  timestamp_ms?: number | null;
}

export interface HabitsBehavioralProfile {
  communication_style: 'structured' | 'spontaneous' | 'analytical' | 'narrative';
  motivation_level: 'high' | 'medium' | 'low';
  self_awareness: 'high' | 'medium' | 'low';
  stress_indicators: 'low' | 'moderate' | 'high';
  overall_recommendation: 'recommended' | 'borderline' | 'not_recommended';
}

export interface HabitsInterviewAnalysisResponse {
  assessment_id: string;
  status: string;
  clarity_score: number;
  relevance_score: number;
  confidence_score: number;
  engagement_score: number;
  emotions_detected: HabitsEmotionMetric[];
  voice_metrics?: HabitsVoiceMetrics | null;
  composite_score: number;
  score_breakdown: Record<string, number>;
  strengths: string[];
  improvement_areas: string[];
  behavioral_profile: HabitsBehavioralProfile;
  processing_time_ms: number;
  modalities_used: string[];
  created_at: string;
}

export interface KnowledgeScores {
  normalized_score?: number;
  overall?: number;
  raw_score?: number;
  confidence_score?: number;
  predicted_filiere?: string;
  filiere_probabilities?: Array<{ filiere: string; probability: number }>;
  filiere_confidence?: string;
  detected_tech_domains?: Record<string, number>;
  detected_skills_ml?: string[];
  domain_breakdown?: Record<string, number>;
  [key: string]: unknown;
}

export interface KnowledgeUploadAssessmentResponse {
  assessment_id: string;
  status: string;
  confidence_score?: number;
  normalized_score?: number | null;
  raw_score?: number | null;
  knowledge_scores?: KnowledgeScores;
  skills?: Array<string | { name: string }>;
  total_experience_years?: number;
}

export interface SkillsUploadAssessmentResponse {
  assessment_id: string;
  status: string;
  project_name?: string;
  overall_scores?: Record<string, number>;
}

export interface CodingChallengeSummary {
  id: string;
  title: string;
  statement: string;
  input_format: string;
  output_format: string;
  constraints: string;
  sample_input: string;
  sample_output: string;
  supported_languages: string[];
  templates: Record<string, string>;
}

export interface CodingChallengeSubmissionRequest {
  challenge_id: string;
  language: string;
  code: string;
}

export interface CodingChallengeSubmissionResponse {
  assessment_id: string;
  ok: boolean;
  score: number;
  passed: number;
  total: number;
  compile_output: string;
  error?: string | null;
  tests: Array<{
    name: string;
    passed: boolean;
    runtime_ms: number;
    expected: string;
    actual: string;
    stderr: string;
  }>;
}

export interface AssessmentActivity {
  id: string;
  module: DomainKey | 'intelligence';
  title: string;
  date: string;
  score: number;
  status: 'completed' | 'in_progress' | 'queued';
}

export interface Insight {
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  supportingData?: Record<string, unknown>;
}

export interface RecommendationItem {
  text: string;
  source: string;
  priority: 'high' | 'medium' | 'low';
}

export interface IntelligenceProfile {
  user_id: string;
  total_assessments: number;
  current_kash_score: {
    overall: number;
    knowledge: number;
    abilities: number;
    skills: number;
    experience: number;
  } | null;
  kash_trend: Array<{
    date: string;
    overall_score: number;
    knowledge_score: number;
    abilities_score: number;
    skills_score: number;
    experience_score: number;
  }>;
  career_insights: Record<string, any>;
  feature_importance_trends: Record<string, any>;
  recommendation_history: Array<{
    recommendation?: string;
    recommendations?: string[];
    priority?: string;
    created_at?: string;
  }>;
  skill_development_progress: Record<string, any>;
  last_assessment?: string;
  career_stage?: string;
  confidence?: number;
}

export interface IntelligenceAssessmentSummaryApi {
  assessment_id: string;
  assessment_name: string;
  status: string;
  created_at: string;
  completed_at?: string;
  overall_score?: number;
  confidence?: number;
  career_stage?: string;
  industry?: string;
  career_goals_count?: number;
  strengths_count?: number;
  recommendations_count?: number;
}

export interface SkillsProfile {
  user_id: string;
  total_assessments: number;
  technical_skills: {
    skills_by_category?: Record<string, Array<{ name: string; confidence: number; proficiency_level: string }>>;
    proficiency_distribution?: Record<string, number>;
    total_unique_skills?: number;
    top_skills?: Array<{ name: string; confidence: number }>;
  };
  programming_languages: Record<string, number>;
  overall_performance: {
    average_score?: number;
    best_score?: number;
    improvement_trend?: string;
    skill_diversity?: number;
    language_diversity?: number;
  };
  project_complexity_trend: Array<{ complexity: number; date: string; project_name: string }>;
  recommendations: string[];
  recent_activity: Array<{
    assessment_id: string;
    project_name: string;
    source_type: string;
    score: number;
    languages: string[];
    completed_at?: string | null;
  }>;
  last_assessment?: string;
}

export interface FeatureImportanceItem {
  feature_name: string;
  feature_value: number;
  shap_value: number;
  contribution_percentage: number;
  direction: 'positive' | 'negative' | 'neutral';
  explanation: string;
}

export interface CareerPathExplanationItem {
  career_path: string;
  match_score: number;
  key_factors: string[];
  skill_gaps: string[];
  alignment_reasons: string[];
  development_needs: string[];
}

export interface AssessmentImpactItem {
  assessment_type: string;
  assessment_name: string;
  score_contribution: number;
  confidence_impact: number;
  improvement_potential: number;
}

export interface RecommendationExplanationItem {
  recommendation: string;
  type: string;
  explanation: string;
  priority: string;
  expected_impact: Record<string, number>;
}

export interface IntelligenceAssessmentDetail {
  assessment_id: string;
  assessment_name: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  kash_score: {
    overall_score: number;
    knowledge_score: number;
    abilities_score: number;
    skills_score: number;
    experience_score: number;
    confidence: number;
    career_stage: string;
    strengths: string[];
    improvement_areas: string[];
    recommendations: string[];
  };
  feature_importance: FeatureImportanceItem[];
  career_explanations: CareerPathExplanationItem[];
  skill_gap_analysis: Array<Record<string, any>>;
  assessment_impacts: AssessmentImpactItem[];
  recommendation_explanations: Record<string, RecommendationExplanationItem>;
  industry?: string;
  career_goals?: string[];
  custom_weights?: Record<string, number> | null;
}

export interface DashboardViewModel {
  lastUpdated: string;
  overallScore: number;
  confidence: number;
  careerStage: string;
  stageTagline: string;
  domainScores: DomainScore[];
  trendPoints: Array<{ date: string; overall: number }>;
  insights: Insight[];
  recommendations: RecommendationItem[];
  assessmentActivity: AssessmentActivity[];
  skillsHighlights: {
    languages: Array<{ name: string; percentage: number }>;
    topSkills: { name: string; confidence: number }[];
  };
}
