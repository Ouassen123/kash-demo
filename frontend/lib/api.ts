import type {
  IntelligenceProfile,
  IntelligenceAssessmentSummaryApi,
  SkillsProfile,
  IntelligenceAssessmentDetail,
  KnowledgeProfile,
  AbilitiesProfile,
  KnowledgeUploadAssessmentResponse,
  SkillsUploadAssessmentResponse,
  CodingChallengeSummary,
  CodingChallengeSubmissionRequest,
  CodingChallengeSubmissionResponse,
  StartAbilitiesAssessmentPayload,
  StartAbilitiesAssessmentResponse,
  SubmitAbilitiesAnswerPayload,
  SubmitAbilitiesAnswerResponse,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';
const API_TOKEN = process.env.NEXT_PUBLIC_API_TOKEN;

function getToken(): string | null {
  if (API_TOKEN) return API_TOKEN;
  if (typeof window !== 'undefined') return localStorage.getItem('kash_token');
  return null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const token = getToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...init?.headers,
  };

  const response = await fetch(url, {
    ...init,
    headers,
    cache: 'no-store',
    next: { revalidate: 0 },
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data as T;
}

export async function fetchIntelligenceProfile() {
  return request<IntelligenceProfile>('/intelligence/profile');
}

export async function fetchIntelligenceAssessments(limit = 5) {
  return request<IntelligenceAssessmentSummaryApi[]>(`/intelligence/assessments?limit=${limit}`);
}

export async function fetchSkillsProfile() {
  return request<SkillsProfile>('/skills/profile');
}

export async function fetchAbilitiesProfile() {
  return request<AbilitiesProfile>('/abilities/profile');
}

export async function startAbilitiesAssessment(payload: StartAbilitiesAssessmentPayload) {
  return request<StartAbilitiesAssessmentResponse>('/abilities/start', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function submitAbilitiesAnswer(payload: SubmitAbilitiesAnswerPayload) {
  return request<SubmitAbilitiesAnswerResponse>('/abilities/submit-answer', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function uploadKnowledgeCv(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/knowledge/upload-cv`, {
    method: 'POST',
    headers: {
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`CV upload failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<KnowledgeUploadAssessmentResponse>;
}

export async function uploadSkillsProject(projectName: string, files: File[]) {
  const formData = new FormData();
  formData.append('project_name', projectName);
  files.forEach((file) => formData.append('files', file));

  const response = await fetch(`${API_BASE_URL}/skills/analyze-upload`, {
    method: 'POST',
    headers: {
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Skills upload failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<SkillsUploadAssessmentResponse>;
}

export async function fetchKnowledgeProfile() {
  return request<KnowledgeProfile>('/knowledge/profile');
}

export async function fetchIntelligenceAssessment(assessmentId: string) {
  return request<IntelligenceAssessmentDetail>(`/intelligence/assessments/${assessmentId}`);
}

export async function fetchCodingChallenges() {
  return request<CodingChallengeSummary[]>(`/skills/coding-challenges`);
}

export async function submitCodingChallenge(payload: CodingChallengeSubmissionRequest) {
  return request<CodingChallengeSubmissionResponse>(`/skills/coding-challenges/submit`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function saveInterviewAnswers(payload: { answers: string[] }) {
  const profile_data = {
    interview: {
      answers: payload.answers,
      created_at: new Date().toISOString(),
    },
  };

  return request<any>(`/auth/me`, {
    method: 'PUT',
    body: JSON.stringify({ profile_data }),
  });
}

export async function generateIntelligenceAssessment(payload?: { industry?: string; career_goals?: string[] }) {
  return request<any>(`/intelligence/assess`, {
    method: 'POST',
    body: JSON.stringify({
      industry: payload?.industry ?? 'technology',
      career_goals: payload?.career_goals ?? ['software_engineer'],
    }),
  });
}

export type DashboardResponse = {
  intelligenceProfile: IntelligenceProfile | null;
  intelligenceAssessments: IntelligenceAssessmentSummaryApi[];
  skillsProfile?: SkillsProfile | null;
  abilitiesProfile?: unknown;
  knowledgeProfile?: unknown;
};

export async function fetchDashboardData(): Promise<DashboardResponse> {
  const [intelligenceProfile, intelligenceAssessments, skillsProfile, abilitiesProfile, knowledgeProfile] = await Promise.all([
    fetchIntelligenceProfile().catch(() => null),
    fetchIntelligenceAssessments(6).catch(() => [] as IntelligenceAssessmentSummaryApi[]),
    fetchSkillsProfile().catch(() => null),
    fetchAbilitiesProfile().catch(() => null),
    fetchKnowledgeProfile().catch(() => null),
  ]);

  return {
    intelligenceProfile,
    intelligenceAssessments,
    skillsProfile: skillsProfile ?? null,
    abilitiesProfile,
    knowledgeProfile,
  };
}
