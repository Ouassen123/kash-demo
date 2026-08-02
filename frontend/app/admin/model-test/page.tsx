'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Brain, FileText, Video, Code, Trophy, FlaskConical,
  PlayCircle, Loader2, CheckCircle2, XCircle, ArrowLeft,
  Activity, Clock, Target, TrendingUp, AlertTriangle,
  Camera, CameraOff, VideoOff,
  Heart, ClipboardList, Wrench,
} from 'lucide-react';
import { useAuth, getStoredToken } from '@/lib/auth-context';
import { getKnowledgeModelStatus, getTrainingHistory } from '@/lib/api';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

type ModelKey = 'knowledge' | 'abilities' | 'habits' | 'skills' | 'intelligence' | 'attitude' | 'psychometric' | 'practical';

interface TestResult {
  success: boolean;
  data: any;
  error: string | null;
  durationMs: number;
}

function safeError(detail: any): string {
  if (!detail) return 'Unknown error';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((d: any) => {
      if (typeof d === 'string') return d;
      if (d?.msg) return `${d.msg}${d.loc ? ` (at: ${Array.isArray(d.loc) ? d.loc.join('.') : d.loc})` : ''}`;
      return JSON.stringify(d);
    }).join('; ');
  }
  if (typeof detail === 'object') {
    if (detail.msg) return detail.msg;
    return JSON.stringify(detail);
  }
  return String(detail);
}

interface ModelStatus {
  loaded: boolean;
  trained: boolean;
  accuracy: number | null;
  details: string;
}

const MODEL_CONFIG: Record<ModelKey, {
  label: string;
  icon: typeof Brain;
  color: string;
  cardClass: string;
  badgeClass: string;
  description: string;
}> = {
  knowledge: {
    label: 'Knowledge',
    icon: FileText,
    color: 'text-knowledge',
    cardClass: 'card-knowledge',
    badgeClass: 'badge-knowledge',
    description: 'Analyse CV — TF-IDF + KNN + ESCO mapping',
  },
  abilities: {
    label: 'Attitude Quiz',
    icon: Brain,
    color: 'text-abilities',
    cardClass: 'card-abilities',
    badgeClass: 'badge-abilities',
    description: 'Entretien comportemental adaptatif — mindset, stress, communication',
  },
  habits: {
    label: 'Habits',
    icon: Video,
    color: 'text-habits',
    cardClass: 'card-habits',
    badgeClass: 'badge-habits',
    description: 'Entretien multimodal — spaCy + clarity/relevance scoring',
  },
  skills: {
    label: 'Skills',
    icon: Code,
    color: 'text-skills',
    cardClass: 'card-skills',
    badgeClass: 'badge-skills',
    description: 'Coding challenges — exécution + tests automatiques',
  },
  intelligence: {
    label: 'Intelligence',
    icon: Trophy,
    color: 'text-intelligence',
    cardClass: 'card-intelligence',
    badgeClass: 'badge-intelligence',
    description: 'KASH scoring global — SHAP + career path analysis',
  },
  attitude: {
    label: 'Attitude',
    icon: Heart,
    color: 'text-abilities',
    cardClass: 'card-abilities',
    badgeClass: 'badge-abilities',
    description: 'Entretien vidéo — mindset, stress, comportement (Big Five signals)',
  },
  psychometric: {
    label: 'Habits (Psy)',
    icon: ClipboardList,
    color: 'text-habits',
    cardClass: 'card-habits',
    badgeClass: 'badge-habits',
    description: 'Questionnaire psychométrique — Big Five + Grit + Discipline',
  },
  practical: {
    label: 'Skills (Practical)',
    icon: Wrench,
    color: 'text-skills',
    cardClass: 'card-skills',
    badgeClass: 'badge-skills',
    description: 'Exercices pratiques adaptatifs — électricité, mécanique, qualité, logistique',
  },
};

export default function ModelTestPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<ModelKey>('knowledge');
  const [knowledgeStatus, setKnowledgeStatus] = useState<any>(null);
  const [knowledgeHistory, setKnowledgeHistory] = useState<any[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem('kash_user');
    if (!stored) { router.push('/login'); return; }
    try {
      const u = JSON.parse(stored);
      if (!u.is_admin) { router.push('/'); return; }
    } catch { router.push('/login'); }
  }, []);

  useEffect(() => {
    const loadKnowledge = async () => {
      try {
        const [status, history] = await Promise.all([
          getKnowledgeModelStatus(),
          getTrainingHistory(),
        ]);
        setKnowledgeStatus(status);
        setKnowledgeHistory(history.history || []);
      } catch {
        setKnowledgeStatus(null);
        setKnowledgeHistory([]);
      }
    };
    loadKnowledge();
  }, []);

  if (loading || !user) return null;

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(91,129,255,0.15),_rgba(4,8,20,0.95))] flex">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 border-r border-white/10 bg-white/2 p-5 flex flex-col gap-6">
        <div>
          <p className="text-xs uppercase tracking-widest text-white/40">KASH Admin</p>
          <p className="text-lg font-bold gradient-text mt-1">Model Testing</p>
        </div>
        <nav className="flex flex-col gap-1">
          <Link href="/admin" className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-white/60 hover:bg-white/5 transition">
            <ArrowLeft size={15} /> Candidats
          </Link>
          <div className="flex items-center gap-2 rounded-xl bg-white/10 px-3 py-2 text-sm text-white">
            <FlaskConical size={15} /> Model Test Lab
          </div>
          <Link href="/knowledge/train-model" className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-white/60 hover:bg-white/5 transition">
            <Brain size={15} /> ML Training
          </Link>
          <Link href="/" className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-white/60 hover:bg-white/5">
            <Trophy size={15} /> Dashboard
          </Link>
        </nav>
        <div className="mt-auto border-t border-white/10 pt-4">
          <p className="text-xs text-white/40">{user.email}</p>
          <p className="text-xs text-amber-300 mt-0.5">Admin</p>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white">Model Test Laboratory</h1>
            <p className="text-sm text-white/60 mt-1">
              Test chaque modèle KASH individuellement — vérifie les résultats, l'efficacité et le statut d'apprentissage.
            </p>
          </div>
        </div>

        {/* Tab bar */}
        <div className="flex items-center gap-2 flex-wrap">
          {(Object.keys(MODEL_CONFIG) as ModelKey[]).map((key) => {
            const cfg = MODEL_CONFIG[key];
            const Icon = cfg.icon;
            return (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`flex items-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-medium transition-all ${
                  activeTab === key
                    ? `${cfg.cardClass} border-white/20 text-white`
                    : 'border-white/10 bg-white/5 text-white/60 hover:bg-white/10'
                }`}
              >
                <Icon size={16} className={cfg.color} />
                {cfg.label}
              </button>
            );
          })}
        </div>

        {/* Active model panel */}
        {activeTab === 'knowledge' && <KnowledgeTester status={knowledgeStatus} history={knowledgeHistory} />}
        {activeTab === 'abilities' && <AttitudeQuizTester />}
        {activeTab === 'habits' && <HabitsTester />}
        {activeTab === 'skills' && <SkillsTester />}
        {activeTab === 'intelligence' && <IntelligenceTester />}
        {activeTab === 'attitude' && <AttitudeTester />}
        {activeTab === 'psychometric' && <PsychometricTester />}
        {activeTab === 'practical' && <PracticalTester />}
      </main>
    </div>
  );
}

// ─── Shared components ───────────────────────────────────────────

function ResultCard({ result, title }: { result: TestResult | null; title: string }) {
  if (!result) return null;
  return (
    <div className={`rounded-2xl border p-5 animate-fade-in ${
      result.success ? 'border-emerald-400/30 bg-emerald-500/5' : 'border-rose-400/30 bg-rose-500/5'
    }`}>
      <div className="flex items-center gap-3 mb-4">
        {result.success ? (
          <CheckCircle2 className="text-emerald-400" size={20} />
        ) : (
          <XCircle className="text-rose-400" size={20} />
        )}
        <p className="text-sm font-bold text-white">{title}</p>
        <span className="ml-auto flex items-center gap-1.5 text-xs text-white/50">
          <Clock size={12} /> {result.durationMs.toFixed(0)}ms
        </span>
      </div>

      {result.error && (
        <div className="rounded-xl bg-rose-500/10 border border-rose-400/20 px-4 py-3 text-sm text-rose-200 mb-3">
          {String(result.error)}
        </div>
      )}

      {result.success && result.data && (
        <ResultDataDisplay data={result.data} />
      )}
    </div>
  );
}

function ResultDataDisplay({ data }: { data: any }) {
  const jsonStr = JSON.stringify(data, null, 2);
  return (
    <div className="space-y-3">
      {/* Key metrics */}
      <div className="grid gap-2 sm:grid-cols-3">
        {typeof data.composite_score === 'number' && (
          <MetricCard label="Composite Score" value={`${data.composite_score.toFixed(1)}`} icon={<Target size={14} />} color="text-aurora" />
        )}
        {typeof data.normalized_score === 'number' && (
          <MetricCard label="Normalized Score" value={`${Math.round(data.normalized_score)}/100`} icon={<TrendingUp size={14} />} color="text-knowledge" />
        )}
        {typeof data.confidence_score === 'number' && (
          <MetricCard label="Confidence" value={`${data.confidence_score.toFixed(1)}%`} icon={<Activity size={14} />} color="text-abilities" />
        )}
        {typeof data.clarity_score === 'number' && (
          <MetricCard label="Clarity" value={`${data.clarity_score.toFixed(1)}`} icon={<Activity size={14} />} color="text-habits" />
        )}
        {typeof data.relevance_score === 'number' && (
          <MetricCard label="Relevance" value={`${data.relevance_score.toFixed(1)}`} icon={<Activity size={14} />} color="text-skills" />
        )}
        {typeof data.score === 'number' && (
          <MetricCard label="Score" value={`${data.score.toFixed(1)}%`} icon={<Target size={14} />} color="text-aurora" />
        )}
        {typeof data.overall_score === 'number' && (
          <MetricCard label="Overall KASH" value={`${data.overall_score.toFixed(1)}`} icon={<Trophy size={14} />} color="text-intelligence" />
        )}
        {typeof data.processing_time_ms === 'number' && (
          <MetricCard label="Processing Time" value={`${data.processing_time_ms.toFixed(0)}ms`} icon={<Clock size={14} />} color="text-mist" />
        )}
        {data.passed !== undefined && data.total !== undefined && (
          <MetricCard label="Tests Passed" value={`${data.passed}/${data.total}`} icon={<CheckCircle2 size={14} />} color="text-emerald-400" />
        )}
      </div>

      {/* Strengths / improvements */}
      {Array.isArray(data.strengths) && data.strengths.length > 0 && (
        <div>
          <p className="text-xs uppercase tracking-widest text-emerald-300/70 mb-2">Strengths</p>
          <div className="flex flex-wrap gap-2">
            {data.strengths.map((s: string, i: number) => (
              <span key={i} className="badge badge-knowledge">{s}</span>
            ))}
          </div>
        </div>
      )}
      {Array.isArray(data.improvement_areas) && data.improvement_areas.length > 0 && (
        <div>
          <p className="text-xs uppercase tracking-widest text-amber-300/70 mb-2">Improvement Areas</p>
          <div className="flex flex-wrap gap-2">
            {data.improvement_areas.map((s: string, i: number) => (
              <span key={i} className="badge badge-skills">{s}</span>
            ))}
          </div>
        </div>
      )}
      {Array.isArray(data.skills) && data.skills.length > 0 && (
        <div>
          <p className="text-xs uppercase tracking-widest text-aurora/70 mb-2">Extracted Skills ({data.skills.length})</p>
          <div className="flex flex-wrap gap-2">
            {data.skills.slice(0, 20).map((s: any, i: number) => (
              <span key={i} className="badge badge-knowledge">{typeof s === 'string' ? s : (s?.name ?? JSON.stringify(s))}</span>
            ))}
            {data.skills.length > 20 && <span className="text-xs text-white/40">+{data.skills.length - 20} more</span>}
          </div>
        </div>
      )}
      {data.score_breakdown && typeof data.score_breakdown === 'object' && (
        <div>
          <p className="text-xs uppercase tracking-widest text-mist/70 mb-2">Score Breakdown</p>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(data.score_breakdown).map(([k, v]: [string, any]) => (
              <div key={k} className="glass-card p-3">
                <p className="text-[10px] uppercase tracking-wider text-white/40">{k.replace(/_/g, ' ')}</p>
                <p className="text-sm font-semibold text-white mt-1">{typeof v === 'number' ? v.toFixed(1) : (typeof v === 'string' ? v : JSON.stringify(v))}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      {data.kash_score && typeof data.kash_score === 'object' && (
        <div>
          <p className="text-xs uppercase tracking-widest text-intelligence/70 mb-2">KASH Score</p>
          <div className="grid gap-2 sm:grid-cols-4">
            {(['knowledge_score', 'abilities_score', 'skills_score', 'overall_score'] as const).map((k) => {
              const v = data.kash_score[k];
              return v !== undefined && (
                <div key={k} className="glass-card p-3 text-center">
                  <p className="text-[10px] uppercase tracking-wider text-white/40">{k.replace(/_/g, ' ')}</p>
                  <p className="text-xl font-bold text-white mt-1">{typeof v === 'number' ? Math.round(v) : (typeof v === 'string' ? v : JSON.stringify(v))}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Raw JSON */}
      <details className="mt-3">
        <summary className="cursor-pointer text-xs text-white/40 hover:text-white/60 transition">Raw JSON response</summary>
        <pre className="mt-2 max-h-80 overflow-auto rounded-xl bg-black/30 p-4 text-xs text-white/70 font-mono whitespace-pre-wrap">{jsonStr}</pre>
      </details>
    </div>
  );
}

function MetricCard({ label, value, icon, color }: { label: string; value: string; icon: React.ReactNode; color: string }) {
  return (
    <div className="glass-card p-3">
      <div className={`flex items-center gap-1.5 ${color} mb-1`}>{icon}<span className="text-[10px] uppercase tracking-wider">{label}</span></div>
      <p className="text-lg font-bold text-white">{value}</p>
    </div>
  );
}

function TestButton({ onClick, loading, disabled, label }: { onClick: () => void; loading: boolean; disabled?: boolean; label: string }) {
  return (
    <button
      onClick={onClick}
      disabled={loading || disabled}
      className="btn-gradient disabled:opacity-50"
    >
      {loading ? <Loader2 size={16} className="animate-spin" /> : <PlayCircle size={16} />}
      {loading ? 'Testing...' : label}
    </button>
  );
}

function ModelStatusBadge({ trained, label }: { trained: boolean; label: string }) {
  return (
    <span className={`badge ${trained ? 'bg-emerald-500/15 text-emerald-300' : 'bg-amber-500/15 text-amber-300'}`}>
      {trained ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
      {label}
    </span>
  );
}

// ─── Knowledge Tester ────────────────────────────────────────────

function KnowledgeTester({ status, history }: { status: any; history: any[] }) {
  const [cvText, setCvText] = useState(`John Doe
Software Engineer

Experience:
- 3 years at TechCorp developing Python web applications with Django and Flask
- Built REST APIs, microservices, and CI/CD pipelines
- Worked with PostgreSQL, Redis, Docker, Kubernetes

Education:
- Master in Computer Science, University of Paris (2020)

Skills: Python, JavaScript, React, Docker, AWS, Git, SQL, TensorFlow, NLP`);
  const [result, setResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(false);

  const runTest = useCallback(async () => {
    setLoading(true);
    setResult(null);
    const t0 = performance.now();
    try {
      const token = getStoredToken();
      const res = await fetch(`${API_BASE}/knowledge/analyze-cv`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ cv_text: cvText, cv_filename: 'test_cv.txt' }),
      });
      const data = await res.json();
      setResult({
        success: res.ok,
        data: res.ok ? data : null,
        error: res.ok ? null : safeError(data.detail ?? `HTTP ${res.status}`),
        durationMs: performance.now() - t0,
      });
    } catch (e: any) {
      setResult({ success: false, data: null, error: e.message, durationMs: performance.now() - t0 });
    } finally {
      setLoading(false);
    }
  }, [cvText]);

  const isTrained = status?.is_trained ?? false;
  const latestRun = history[history.length - 1] ?? null;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Model status */}
      <div className="glass-card card-knowledge p-5 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="flex items-center gap-2">
              <FileText className="text-knowledge" size={20} />
              <h2 className="text-xl font-bold text-white">Knowledge Model</h2>
            </div>
            <p className="text-sm text-white/60 mt-1">{MODEL_CONFIG.knowledge.description}</p>
          </div>
          <ModelStatusBadge trained={isTrained} label={isTrained ? 'Trained & Ready' : 'Needs Training'} />
        </div>

        <div className="grid gap-3 sm:grid-cols-4">
          <div className="glass-card p-3">
            <p className="text-[10px] uppercase tracking-wider text-white/40">Status</p>
            <p className="text-sm font-semibold text-white mt-1">{isTrained ? 'Ready' : 'Not trained'}</p>
          </div>
          <div className="glass-card p-3">
            <p className="text-[10px] uppercase tracking-wider text-white/40">Features</p>
            <p className="text-sm font-semibold text-white mt-1">{status?.n_features ?? '—'}</p>
          </div>
          <div className="glass-card p-3">
            <p className="text-[10px] uppercase tracking-wider text-white/40">CV Accuracy</p>
            <p className="text-sm font-semibold text-emerald-300 mt-1">
              {status?.training_report?.cv_accuracy != null
                ? `${(status.training_report.cv_accuracy * 100).toFixed(1)}%`
                : '—'}
            </p>
          </div>
          <div className="glass-card p-3">
            <p className="text-[10px] uppercase tracking-wider text-white/40">Algorithm</p>
            <p className="text-sm font-semibold text-white mt-1">{status?.training_report?.best_algorithm ?? '—'}</p>
          </div>
        </div>

        {latestRun && (
          <div className="rounded-xl bg-white/5 border border-white/10 p-3 text-xs text-white/60">
            <span className="text-white/40">Latest training:</span>{' '}
            {new Date(latestRun.trained_at).toLocaleString('fr-FR')} —{' '}
            <span className="text-emerald-300">Train {(latestRun.train_accuracy * 100).toFixed(1)}%</span> /{' '}
            <span className="text-aurora">CV {(latestRun.cv_accuracy * 100).toFixed(1)}%</span> —{' '}
            {latestRun.best_algorithm} — SMOTE {latestRun.smote_applied ? 'On' : 'Off'}
          </div>
        )}
      </div>

      {/* Test input */}
      <div className="glass-card p-5 space-y-4">
        <p className="text-sm font-semibold text-white">Test: Analyze CV text</p>
        <textarea
          value={cvText}
          onChange={(e) => setCvText(e.target.value)}
          className="w-full min-h-[200px] rounded-xl border border-white/15 bg-black/20 p-4 text-sm text-white/90 font-mono"
          placeholder="Paste CV text here..."
        />
        <TestButton onClick={runTest} loading={loading} label="Run CV Analysis" />
      </div>

      <ResultCard result={result} title="Knowledge Model — CV Analysis Result" />
    </div>
  );
}

// ─── Attitude Quiz Tester ──────────────────────────────────────

function AttitudeQuizTester() {
  const [domain, setDomain] = useState('memory');
  const [numQuestions, setNumQuestions] = useState(5);
  const [result, setResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [sessionInfo, setSessionInfo] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [currentQ, setCurrentQ] = useState<any>(null);
  const [questionNum, setQuestionNum] = useState(0);
  const [finalResult, setFinalResult] = useState<TestResult | null>(null);

  const startTest = useCallback(async () => {
    setLoading(true);
    setResult(null);
    setSessionInfo(null);
    setCurrentQ(null);
    setAnswers({});
    setFinalResult(null);
    const t0 = performance.now();
    try {
      const token = getStoredToken();
      const res = await fetch(`${API_BASE}/abilities/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          quiz_type: 'cognitive',
          domain: domain,
          num_questions: numQuestions,
          adaptive: true,
        }),
      });
      const data = await res.json();
      setResult({
        success: res.ok,
        data: res.ok ? data : null,
        error: res.ok ? null : safeError(data.detail ?? `HTTP ${res.status}`),
        durationMs: performance.now() - t0,
      });
      if (res.ok) {
        setSessionInfo(data);
        setCurrentQ(data.current_question);
        setQuestionNum(1);
      }
    } catch (e: any) {
      setResult({ success: false, data: null, error: e.message, durationMs: performance.now() - t0 });
    } finally {
      setLoading(false);
    }
  }, [domain, numQuestions]);

  const submitAnswer = useCallback(async (questionId: string, answer: string) => {
    if (!sessionInfo) return;
    setLoading(true);
    const t0 = performance.now();
    try {
      const token = getStoredToken();
      const res = await fetch(`${API_BASE}/abilities/submit-answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          session_id: sessionInfo.session_id,
          question_id: questionId,
          answer: answer,
          response_time_ms: 3000,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        if (data.quiz_completed) {
          setFinalResult({
            success: true,
            data: data,
            error: null,
            durationMs: performance.now() - t0,
          });
          setCurrentQ(null);
        } else {
          setCurrentQ(data.next_question);
          setQuestionNum(data.question_number);
        }
      } else {
        setFinalResult({
          success: false,
          data: null,
          error: safeError(data.detail ?? `HTTP ${res.status}`),
          durationMs: performance.now() - t0,
        });
      }
    } catch (e: any) {
      setFinalResult({ success: false, data: null, error: e.message, durationMs: performance.now() - t0 });
    } finally {
      setLoading(false);
    }
  }, [sessionInfo]);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Model status */}
      <div className="glass-card card-abilities p-5 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Brain className="text-abilities" size={20} />
              <h2 className="text-xl font-bold text-white">Attitude Model</h2>
            </div>
            <p className="text-sm text-white/60 mt-1">{MODEL_CONFIG.abilities.description}</p>
          </div>
          <ModelStatusBadge trained={true} label="Always Ready (rule-based IRT)" />
        </div>
      </div>

      {/* Config + start */}
      <div className="glass-card p-5 space-y-4">
        <p className="text-sm font-semibold text-white">Test: Start adaptive quiz</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-xs text-white/70">
            Cognitive Domain
            <select value={domain} onChange={(e) => setDomain(e.target.value)}
              className="mt-1 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm text-white">
              <option value="memory">Memory</option>
              <option value="logic">Logic</option>
              <option value="attention">Attention</option>
              <option value="spatial">Spatial</option>
            </select>
          </label>
          <label className="block text-xs text-white/70">
            Number of Questions
            <select value={numQuestions} onChange={(e) => setNumQuestions(Number(e.target.value))}
              className="mt-1 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm text-white">
              <option value={3}>3</option>
              <option value={5}>5</option>
              <option value={10}>10</option>
            </select>
          </label>
        </div>
        <TestButton onClick={startTest} loading={loading} label="Start Attitude Test" />
      </div>

      <ResultCard result={result} title="Attitude — Quiz Started" />

      {/* Interactive quiz */}
      {currentQ && sessionInfo && (
        <div className="glass-card card-abilities p-5 space-y-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-white">Question {questionNum} / {sessionInfo.total_questions}</p>
            <span className="badge badge-abilities">Adaptive</span>
          </div>
          <p className="text-sm text-white/90 font-medium">{currentQ.question_text}</p>
          <div className="space-y-2">
            {currentQ.options?.map((opt: string) => (
              <button
                key={opt}
                onClick={() => submitAnswer(currentQ.id, opt)}
                disabled={loading}
                className="block w-full text-left rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/80 hover:bg-abilities/10 hover:border-abilities/30 transition disabled:opacity-50"
              >
                {opt}
              </button>
            ))}
          </div>
          {loading && <p className="text-xs text-white/50 flex items-center gap-2"><Loader2 size={14} className="animate-spin" /> Submitting...</p>}
        </div>
      )}

      <ResultCard result={finalResult} title="Attitude — Quiz Final Results" />
    </div>
  );
}

// ─── Habits Tester ───────────────────────────────────────────────

function HabitsTester() {
  const [answers, setAnswers] = useState([
    { question_id: 'q1', question_text: 'Present your main academic or professional goal.', answer_text: 'My main goal is to become a senior software engineer specializing in AI and machine learning. I want to build intelligent systems that help people make better decisions.' },
    { question_id: 'q2', question_text: 'Describe a challenge you solved and what you learned.', answer_text: 'I faced a critical performance issue in our API that was causing timeouts. I profiled the system, identified the bottleneck in database queries, added proper indexes, and implemented caching. I learned the importance of monitoring and proactive optimization.' },
    { question_id: 'q3', question_text: 'What skills do you want to improve in the next 3 months?', answer_text: 'I want to improve my skills in deep learning, particularly transformer architectures and NLP. I also want to strengthen my system design skills for scalable ML infrastructure.' },
  ]);
  const [result, setResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(false);

  // Camera state
  const [videoEl, setVideoEl] = useState<HTMLVideoElement | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [cameraOn, setCameraOn] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [capturedFrames, setCapturedFrames] = useState<string[]>([]);

  const startCamera = useCallback(async () => {
    setCameraError(null);
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 }, audio: false });
      setStream(s);
      setCameraOn(true);
    } catch (e: any) {
      setCameraError(e.message ?? 'Failed to access camera');
      setCameraOn(false);
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      setStream(null);
    }
    setCameraOn(false);
  }, [stream]);

  const captureFrame = useCallback(() => {
    if (!videoEl) return;
    const canvas = document.createElement('canvas');
    canvas.width = 320;
    canvas.height = 240;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(videoEl, 0, 0, 320, 240);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
    const base64 = dataUrl.split(',')[1];
    setCapturedFrames(prev => [...prev, base64]);
  }, [videoEl]);

  const clearFrames = useCallback(() => setCapturedFrames([]), []);

  useEffect(() => {
    return () => {
      if (stream) stream.getTracks().forEach(t => t.stop());
    };
  }, [stream]);

  const runTest = useCallback(async () => {
    setLoading(true);
    setResult(null);
    const t0 = performance.now();
    try {
      const token = getStoredToken();
      const res = await fetch(`${API_BASE}/habits/interview/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          answers: answers.map(a => ({
            question_id: a.question_id,
            question_text: a.question_text,
            answer_text: a.answer_text,
          })),
          audio_base64: '',
          video_frames_base64: capturedFrames,
          industry: 'technology',
        }),
      });
      const data = await res.json();
      setResult({
        success: res.ok,
        data: res.ok ? data : null,
        error: res.ok ? null : safeError(data.detail ?? `HTTP ${res.status}`),
        durationMs: performance.now() - t0,
      });
    } catch (e: any) {
      setResult({ success: false, data: null, error: e.message, durationMs: performance.now() - t0 });
    } finally {
      setLoading(false);
    }
  }, [answers, capturedFrames]);

  const updateAnswer = (idx: number, text: string) => {
    setAnswers(prev => prev.map((a, i) => i === idx ? { ...a, answer_text: text } : a));
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Model status */}
      <div className="glass-card card-habits p-5 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Video className="text-habits" size={20} />
              <h2 className="text-xl font-bold text-white">Habits Model</h2>
            </div>
            <p className="text-sm text-white/60 mt-1">{MODEL_CONFIG.habits.description}</p>
          </div>
          <ModelStatusBadge trained={true} label="Ready (spaCy NLP)" />
        </div>
      </div>

      {/* Camera section */}
      <div className="glass-card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-white flex items-center gap-2">
            <Camera size={16} className="text-habits" /> Webcam Capture
          </p>
          <div className="flex items-center gap-2">
            {!cameraOn ? (
              <button onClick={startCamera} className="btn-ghost text-xs">
                <Camera size={14} /> Start Camera
              </button>
            ) : (
              <button onClick={stopCamera} className="btn-ghost text-xs text-rose-300">
                <CameraOff size={14} /> Stop Camera
              </button>
            )}
          </div>
        </div>

        {cameraError && (
          <div className="rounded-xl bg-rose-500/10 border border-rose-400/20 px-4 py-3 text-sm text-rose-200">
            {cameraError}
          </div>
        )}

        <div className="flex items-start gap-4 flex-wrap">
          {/* Video preview */}
          <div className="relative rounded-xl overflow-hidden border border-white/15 bg-black/40" style={{ width: 320, height: 240 }}>
            {cameraOn ? (
              <video
                ref={(el) => { if (el && el !== videoEl) { setVideoEl(el); el.srcObject = stream; el.play().catch(() => {}); } }}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="flex items-center justify-center w-full h-full text-white/30">
                <div className="text-center">
                  <VideoOff size={32} className="mx-auto mb-2" />
                  <p className="text-xs">Camera off</p>
                </div>
              </div>
            )}
          </div>

          {/* Captured frames */}
          <div className="flex-1 min-w-[200px] space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-xs text-white/50">Captured frames: {capturedFrames.length}</p>
              {capturedFrames.length > 0 && (
                <button onClick={clearFrames} className="text-xs text-rose-300 hover:text-rose-200">Clear</button>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {capturedFrames.map((frame, i) => (
                <img
                  key={i}
                  src={`data:image/jpeg;base64,${frame}`}
                  alt={`Frame ${i + 1}`}
                  className="w-20 h-16 object-cover rounded-lg border border-white/15"
                />
              ))}
            </div>
            {cameraOn && (
              <button onClick={captureFrame} className="btn-ghost text-xs">
                <Camera size={14} /> Capture Frame
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Test input */}
      <div className="glass-card p-5 space-y-4">
        <p className="text-sm font-semibold text-white">Test: Analyze interview answers</p>
        {answers.map((a, idx) => (
          <div key={idx} className="space-y-2">
            <p className="text-xs text-white/50 uppercase tracking-wider">Q{idx + 1}: {a.question_text}</p>
            <textarea
              value={a.answer_text}
              onChange={(e) => updateAnswer(idx, e.target.value)}
              className="w-full min-h-[80px] rounded-xl border border-white/15 bg-black/20 p-3 text-sm text-white/90"
              rows={3}
            />
          </div>
        ))}
        <TestButton onClick={runTest} loading={loading} label="Run Interview Analysis" />
      </div>

      <ResultCard result={result} title="Habits — Interview Analysis Result" />
    </div>
  );
}

// ─── Skills Tester ───────────────────────────────────────────────

function SkillsTester() {
  const [challenges, setChallenges] = useState<any[]>([]);
  const [challengeId, setChallengeId] = useState('balanced-brackets-v1');
  const [language, setLanguage] = useState('python');
  const [code, setCode] = useState(`def solve(s):
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for c in s:
        if c in '([{':
            stack.append(c)
        elif c in ')]}':
            if not stack or stack[-1] != pairs[c]:
                return False
            stack.pop()
    return len(stack) == 0
`);
  const [result, setResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = getStoredToken();
    fetch(`${API_BASE}/skills/coding-challenges`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => { setChallenges(d); const first = d.find((c: any) => c.id === 'balanced-brackets-v1') ?? d[0]; if (first) setChallengeId(first.id); })
      .catch(() => {});
  }, []);

  const runTest = useCallback(async () => {
    setLoading(true);
    setResult(null);
    const t0 = performance.now();
    try {
      const token = getStoredToken();
      const res = await fetch(`${API_BASE}/skills/coding-challenges/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ challenge_id: challengeId, language, code }),
      });
      const data = await res.json();
      setResult({
        success: res.ok,
        data: res.ok ? data : null,
        error: res.ok ? null : safeError(data.detail ?? `HTTP ${res.status}`),
        durationMs: performance.now() - t0,
      });
    } catch (e: any) {
      setResult({ success: false, data: null, error: e.message, durationMs: performance.now() - t0 });
    } finally {
      setLoading(false);
    }
  }, [challengeId, language, code]);

  const selectedChallenge = challenges.find(c => c.id === challengeId);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Model status */}
      <div className="glass-card card-skills p-5 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Code className="text-skills" size={20} />
              <h2 className="text-xl font-bold text-white">Skills Model</h2>
            </div>
            <p className="text-sm text-white/60 mt-1">{MODEL_CONFIG.skills.description}</p>
          </div>
          <ModelStatusBadge trained={true} label="Ready (sandbox executor)" />
        </div>
      </div>

      {/* Test input */}
      <div className="glass-card p-5 space-y-4">
        <p className="text-sm font-semibold text-white">Test: Submit coding challenge</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-xs text-white/70">
            Challenge
            <select value={challengeId} onChange={(e) => setChallengeId(e.target.value)}
              className="mt-1 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm text-white">
              {challenges.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}
            </select>
          </label>
          <label className="block text-xs text-white/70">
            Language
            <select value={language} onChange={(e) => setLanguage(e.target.value)}
              className="mt-1 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm text-white">
              <option value="python">Python</option>
              <option value="cpp">C++</option>
              <option value="javascript">JavaScript</option>
              <option value="java">Java</option>
            </select>
          </label>
        </div>

        {selectedChallenge && (
          <div className="rounded-xl border border-white/10 bg-black/20 p-3">
            <p className="text-[10px] uppercase tracking-widest text-white/40 mb-1">Statement</p>
            <pre className="text-xs text-white/70 whitespace-pre-wrap">{selectedChallenge.statement}</pre>
          </div>
        )}

        <label className="block text-xs text-white/70">
          Code
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="mt-1 w-full min-h-[260px] rounded-xl border border-white/15 bg-black/30 p-3 font-mono text-xs text-white/80"
            spellCheck={false}
          />
        </label>
        <TestButton onClick={runTest} loading={loading} label="Run Code Test" />
      </div>

      <ResultCard result={result} title="Skills — Coding Challenge Result" />
    </div>
  );
}

// ─── Intelligence Tester ─────────────────────────────────────────

function IntelligenceTester() {
  const [industry, setIndustry] = useState('technology');
  const [result, setResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(false);

  const runTest = useCallback(async () => {
    setLoading(true);
    setResult(null);
    const t0 = performance.now();
    try {
      const token = getStoredToken();
      const res = await fetch(`${API_BASE}/intelligence/assess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          industry: industry,
          career_goals: ['software_engineer'],
        }),
      });
      const data = await res.json();
      setResult({
        success: res.ok,
        data: res.ok ? data : null,
        error: res.ok ? null : safeError(data.detail ?? `HTTP ${res.status}`),
        durationMs: performance.now() - t0,
      });
    } catch (e: any) {
      setResult({ success: false, data: null, error: e.message, durationMs: performance.now() - t0 });
    } finally {
      setLoading(false);
    }
  }, [industry]);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Model status */}
      <div className="glass-card card-intelligence p-5 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Trophy className="text-intelligence" size={20} />
              <h2 className="text-xl font-bold text-white">Intelligence Model</h2>
            </div>
            <p className="text-sm text-white/60 mt-1">{MODEL_CONFIG.intelligence.description}</p>
          </div>
          <ModelStatusBadge trained={true} label="Ready (KASH Scorer + SHAP)" />
        </div>
      </div>

      {/* Test input */}
      <div className="glass-card p-5 space-y-4">
        <p className="text-sm font-semibold text-white">Test: Generate intelligence assessment</p>
        <div className="rounded-xl bg-intelligence/10 border border-intelligence/20 p-3 text-xs text-white/60">
          This requires that the current user has at least one assessment in each KASH domain (Knowledge, Attitude, Skills, Habits).
          The model aggregates all scores and produces the final KASH composite with SHAP explanations.
        </div>
        <label className="block text-xs text-white/70">
          Industry
          <select value={industry} onChange={(e) => setIndustry(e.target.value)}
            className="mt-1 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm text-white">
            <option value="technology">Technology</option>
            <option value="finance">Finance</option>
            <option value="healthcare">Healthcare</option>
            <option value="education">Education</option>
            <option value="manufacturing">Manufacturing</option>
          </select>
        </label>
        <TestButton onClick={runTest} loading={loading} label="Run Intelligence Assessment" />
      </div>

      <ResultCard result={result} title="Intelligence — KASH Assessment Result" />
    </div>
  );
}

// ─── Attitude Tester (A) — Video Interview ─────────────────────────

function AttitudeTester() {
  const [questions, setQuestions] = useState<any[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [cameraOn, setCameraOn] = useState(false);
  const [capturedFrames, setCapturedFrames] = useState<string[]>([]);
  const [videoEl, setVideoEl] = useState<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/attitude/questions`)
      .then(r => r.json())
      .then(data => {
        setQuestions(data);
        const init: Record<string, string> = {};
        data.forEach((q: any) => { init[q.id] = ''; });
        setAnswers(init);
      })
      .catch(() => {});
  }, []);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoEl) videoEl.srcObject = stream;
      setCameraOn(true);
    } catch (e: any) {
      setCameraOn(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t: MediaStreamTrack) => t.stop());
      streamRef.current = null;
    }
    setCameraOn(false);
  };

  const captureFrame = () => {
    if (!videoEl) return;
    const canvas = document.createElement('canvas');
    canvas.width = 320;
    canvas.height = 240;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(videoEl, 0, 0, 320, 240);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
    setCapturedFrames(prev => [...prev, dataUrl]);
  };

  const clearFrames = () => setCapturedFrames([]);

  const runTest = useCallback(async () => {
    setLoading(true);
    setResult(null);
    const t0 = performance.now();
    try {
      const token = getStoredToken();
      const res = await fetch(`${API_BASE}/attitude/interview/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          answers: questions.map(q => ({
            question_id: q.id,
            question_text: q.text,
            answer_text: answers[q.id] || '',
          })),
          video_frames_base64: capturedFrames.map(f => f.split(',')[1] || ''),
          audio_base64: '',
          industry: 'technology',
        }),
      });
      const data = await res.json();
      setResult({
        success: res.ok,
        data: res.ok ? data : null,
        error: res.ok ? null : safeError(data.detail ?? `HTTP ${res.status}`),
        durationMs: performance.now() - t0,
      });
    } catch (e: any) {
      setResult({ success: false, data: null, error: e.message, durationMs: performance.now() - t0 });
    } finally {
      setLoading(false);
    }
  }, [questions, answers, capturedFrames]);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="glass-card card-abilities p-5 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Heart className="text-abilities" size={20} />
              <h2 className="text-xl font-bold text-white">Attitude Model (A)</h2>
            </div>
            <p className="text-sm text-white/60 mt-1">{MODEL_CONFIG.attitude.description}</p>
          </div>
          <ModelStatusBadge trained={true} label="Ready (Behavioral + NLP)" />
        </div>
      </div>

      <div className="glass-card p-5 space-y-4">
        <p className="text-sm font-semibold text-white">Entretien comportemental — répondez aux questions</p>
        {questions.map((q, idx) => (
          <div key={q.id} className="space-y-2">
            <p className="text-xs text-white/50 uppercase tracking-wider">Q{idx + 1} [{q.category}]: {q.text}</p>
            <textarea
              value={answers[q.id] || ''}
              onChange={(e) => setAnswers(prev => ({ ...prev, [q.id]: e.target.value }))}
              className="w-full min-h-[80px] rounded-xl border border-white/15 bg-black/20 p-3 text-sm text-white/90"
              rows={3}
              placeholder="Tapez votre réponse..."
            />
          </div>
        ))}

        <div className="border-t border-white/10 pt-4 space-y-3">
          <p className="text-sm font-semibold text-white">Webcam (optionnel — capture des frames pour analyse faciale)</p>
          <div className="flex items-center gap-3 flex-wrap">
            {!cameraOn ? (
              <button onClick={startCamera} className="flex items-center gap-2 rounded-lg bg-abilities/20 px-3 py-2 text-sm text-abilities hover:bg-abilities/30">
                <Camera size={16} /> Activer caméra
              </button>
            ) : (
              <button onClick={stopCamera} className="flex items-center gap-2 rounded-lg bg-red-500/20 px-3 py-2 text-sm text-red-400 hover:bg-red-500/30">
                <CameraOff size={16} /> Arrêter caméra
              </button>
            )}
            {cameraOn && (
              <button onClick={captureFrame} className="flex items-center gap-2 rounded-lg bg-white/10 px-3 py-2 text-sm text-white hover:bg-white/20">
                <Video size={16} /> Capturer frame
              </button>
            )}
            {capturedFrames.length > 0 && (
              <button onClick={clearFrames} className="flex items-center gap-2 rounded-lg bg-white/10 px-3 py-2 text-sm text-white/60 hover:bg-white/20">
                Clear ({capturedFrames.length})
              </button>
            )}
          </div>
          <video
            ref={(el) => { if (el && el !== videoEl) setVideoEl(el); }}
            autoPlay
            playsInline
            muted
            className={`w-full max-w-xs rounded-xl border border-white/15 ${cameraOn ? '' : 'hidden'}`}
          />
          {capturedFrames.length > 0 && (
            <div className="flex gap-2 flex-wrap">
              {capturedFrames.map((f, i) => (
                <img key={i} src={f} alt={`Frame ${i}`} className="w-20 h-16 rounded-lg border border-white/15 object-cover" />
              ))}
            </div>
          )}
        </div>

        <TestButton onClick={runTest} loading={loading} label="Run Attitude Analysis" />
      </div>

      <ResultCard result={result} title="Attitude — Behavioral Interview Result" />
    </div>
  );
}

// ─── Psychometric Tester (H) — Questionnaire ──────────────────────

function PsychometricTester() {
  const [questions, setQuestions] = useState<any[]>([]);
  const [responses, setResponses] = useState<Record<string, number>>({});
  const [result, setResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/habits/psychometric/questions`)
      .then(r => r.json())
      .then(data => {
        setQuestions(data);
        const init: Record<string, number> = {};
        data.forEach((q: any) => { init[q.id] = 3; });
        setResponses(init);
      })
      .catch(() => {});
  }, []);

  const runTest = useCallback(async () => {
    setLoading(true);
    setResult(null);
    const t0 = performance.now();
    try {
      const token = getStoredToken();
      const res = await fetch(`${API_BASE}/habits/psychometric/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          responses: Object.entries(responses).map(([question_id, answer]) => ({ question_id, answer })),
        }),
      });
      const data = await res.json();
      setResult({
        success: res.ok,
        data: res.ok ? data : null,
        error: res.ok ? null : safeError(data.detail ?? `HTTP ${res.status}`),
        durationMs: performance.now() - t0,
      });
    } catch (e: any) {
      setResult({ success: false, data: null, error: e.message, durationMs: performance.now() - t0 });
    } finally {
      setLoading(false);
    }
  }, [responses]);

  const scaleLabels = ['Pas du tout d\'accord', 'Pas d\'accord', 'Neutre', 'D\'accord', 'Tout à fait d\'accord'];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="glass-card card-habits p-5 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="flex items-center gap-2">
              <ClipboardList className="text-habits" size={20} />
              <h2 className="text-xl font-bold text-white">Habits — Psychometric Questionnaire</h2>
            </div>
            <p className="text-sm text-white/60 mt-1">{MODEL_CONFIG.psychometric.description}</p>
          </div>
          <ModelStatusBadge trained={true} label="Validated (Big Five + Grit)" />
        </div>
      </div>

      <div className="glass-card p-5 space-y-4">
        <p className="text-sm font-semibold text-white">Questionnaire psychométrique — 20 questions</p>
        {questions.map((q, idx) => (
          <div key={q.id} className="space-y-2">
            <p className="text-sm text-white/80">
              <span className="text-white/40 text-xs mr-2">Q{idx + 1}</span>
              {q.text}
              <span className="ml-2 text-xs text-white/30">[{q.dimension}]</span>
            </p>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map(val => (
                <button
                  key={val}
                  onClick={() => setResponses(prev => ({ ...prev, [q.id]: val }))}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                    responses[q.id] === val
                      ? 'bg-habits/30 text-habits border border-habits/40'
                      : 'bg-white/5 text-white/50 hover:bg-white/10 border border-white/10'
                  }`}
                  title={scaleLabels[val - 1]}
                >
                  {val}
                </button>
              ))}
            </div>
          </div>
        ))}
        <TestButton onClick={runTest} loading={loading} label="Submit & Score Questionnaire" />
      </div>

      <ResultCard result={result} title="Habits — Psychometric Profile Result" />
    </div>
  );
}

// ─── Practical Tester (S) — Domain-Adaptive Challenges ────────────

function PracticalTester() {
  const [challenges, setChallenges] = useState<any[]>([]);
  const [selectedChallenge, setSelectedChallenge] = useState<any | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [domainFilter, setDomainFilter] = useState('');
  const [cvText, setCvText] = useState('');
  const [recommendation, setRecommendation] = useState<any | null>(null);
  const [cvLoading, setCvLoading] = useState(false);
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);

  useEffect(() => {
    const url = domainFilter
      ? `${API_BASE}/skills/practical/challenges?domain=${domainFilter}`
      : `${API_BASE}/skills/practical/challenges`;
    fetch(url)
      .then(r => r.json())
      .then(data => setChallenges(data))
      .catch(() => setChallenges([]));
  }, [domainFilter]);

  const analyzePDF = useCallback(async () => {
    if (!cvFile) return;
    setPdfLoading(true);
    setRecommendation(null);
    try {
      const formData = new FormData();
      formData.append('file', cvFile);
      const res = await fetch(`${API_BASE}/skills/practical/recommend-pdf?top_n=3`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setRecommendation(data);
        setChallenges(data.recommended_challenges || []);
      } else {
        console.error('PDF recommendation failed:', data.detail);
      }
    } catch (e: any) {
      console.error('PDF upload failed:', e);
    } finally {
      setPdfLoading(false);
    }
  }, [cvFile]);

  const analyzeCV = useCallback(async () => {
    if (cvText.trim().length < 50) return;
    setCvLoading(true);
    setRecommendation(null);
    try {
      const res = await fetch(`${API_BASE}/skills/practical/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cv_text: cvText, top_n: 3 }),
      });
      const data = await res.json();
      if (res.ok) {
        setRecommendation(data);
        setChallenges(data.recommended_challenges || []);
      }
    } catch (e: any) {
      console.error('CV recommendation failed:', e);
    } finally {
      setCvLoading(false);
    }
  }, [cvText]);

  const selectChallenge = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/skills/practical/challenges/${id}`);
      const data = await res.json();
      setSelectedChallenge(data);
      const init: Record<string, string> = {};
      data.test_cases?.forEach((tc: any) => { init[tc.name] = ''; });
      setAnswers(init);
      setResult(null);
    } catch {}
  };

  const runTest = useCallback(async () => {
    if (!selectedChallenge) return;
    setLoading(true);
    setResult(null);
    const t0 = performance.now();
    try {
      const token = getStoredToken();
      const res = await fetch(`${API_BASE}/skills/practical/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          challenge_id: selectedChallenge.id,
          answers,
        }),
      });
      const data = await res.json();
      setResult({
        success: res.ok,
        data: res.ok ? data : null,
        error: res.ok ? null : safeError(data.detail ?? `HTTP ${res.status}`),
        durationMs: performance.now() - t0,
      });
    } catch (e: any) {
      setResult({ success: false, data: null, error: e.message, durationMs: performance.now() - t0 });
    } finally {
      setLoading(false);
    }
  }, [selectedChallenge, answers]);

  const domains = ['', 'electrical', 'mechanical', 'quality', 'logistics', 'management'];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="glass-card card-skills p-5 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Wrench className="text-skills" size={20} />
              <h2 className="text-xl font-bold text-white">Skills — Practical Challenges</h2>
            </div>
            <p className="text-sm text-white/60 mt-1">{MODEL_CONFIG.practical.description}</p>
          </div>
          <ModelStatusBadge trained={true} label="Domain-Adaptive" />
        </div>
      </div>

      {/* CV → Domain detection → Recommended challenges */}
      <div className="glass-card p-5 space-y-4">
        <div className="flex items-center gap-2">
          <FileText className="text-skills" size={18} />
          <p className="text-sm font-semibold text-white">Détection de domaine depuis CV</p>
        </div>

        {/* PDF Upload */}
        <div className="rounded-xl border border-skills/20 bg-skills/5 p-4 space-y-3">
          <p className="text-xs font-medium text-skills">Upload PDF / DOCX / TXT</p>
          <div className="flex items-center gap-3">
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(e) => setCvFile(e.target.files?.[0] ?? null)}
              className="text-xs text-white/70 file:mr-3 file:rounded-lg file:border-0 file:bg-skills/20 file:px-4 file:py-2 file:text-skills hover:file:bg-skills/30"
            />
            <button
              onClick={analyzePDF}
              disabled={!cvFile || pdfLoading}
              className="px-4 py-2 rounded-xl text-sm font-medium bg-skills/20 text-skills border border-skills/40 hover:bg-skills/30 transition disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {pdfLoading ? <Loader2 className="animate-spin" size={16} /> : 'Uploader & Analyser'}
            </button>
          </div>
          {cvFile && (
            <p className="text-xs text-white/40">Fichier sélectionné : {cvFile.name} ({Math.round(cvFile.size / 1024)} KB)</p>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-white/40">
          <div className="h-px flex-1 bg-white/10" />
          OU
          <div className="h-px flex-1 bg-white/10" />
        </div>

        {/* Text paste */}
        <p className="text-xs text-white/50">Collez le texte du CV — le système détectera la filière (ex: Génie Électrique) et proposera les exercices adaptés.</p>
        <textarea
          value={cvText}
          onChange={(e) => setCvText(e.target.value)}
          className="w-full min-h-[120px] rounded-xl border border-white/15 bg-black/20 p-3 text-sm text-white/90"
          rows={5}
          placeholder="Collez ici le texte du CV de l'étudiant..."
        />
        <div className="flex items-center gap-3">
          <button
            onClick={analyzeCV}
            disabled={cvLoading || cvText.trim().length < 50}
            className="px-4 py-2 rounded-xl text-sm font-medium bg-skills/20 text-skills border border-skills/40 hover:bg-skills/30 transition disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {cvLoading ? <Loader2 className="animate-spin" size={16} /> : 'Analyser le texte & Recommander'}
          </button>
          {cvText.trim().length > 0 && cvText.trim().length < 50 && (
            <span className="text-xs text-white/40">Minimum 50 caractères</span>
          )}
        </div>
        {recommendation && (
          <div className="rounded-xl bg-skills/10 border border-skills/20 p-4 space-y-3">
            {recommendation.predicted_filiere && (
              <div className="space-y-1">
                <p className="text-xs font-semibold text-skills">Filière détectée :</p>
                <p className="text-sm text-white font-bold">{recommendation.predicted_filiere}</p>
              </div>
            )}
            <div className="space-y-1">
              <p className="text-xs font-semibold text-skills">Domaines techniques détectés :</p>
              <div className="flex gap-2 flex-wrap">
                {Object.entries(recommendation.detected_tech_domains || {}).map(([domain, hits]: any) => (
                  <span key={domain} className="px-2 py-1 rounded-lg text-xs bg-skills/20 text-skills border border-skills/30">
                    {domain}: {hits} hits
                  </span>
                ))}
              </div>
            </div>
            {recommendation.detected_skills && recommendation.detected_skills.length > 0 && (
              <div className="space-y-1">
                <p className="text-xs font-semibold text-skills">Skills extraits ({recommendation.detected_skills.length}) :</p>
                <div className="flex gap-1.5 flex-wrap">
                  {recommendation.detected_skills.map((s: string) => (
                    <span key={s} className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-white/60">{s}</span>
                  ))}
                </div>
              </div>
            )}
            <p className="text-xs text-white/50">{recommendation.recommended_challenges?.length} challenge(s) recommandé(s) pour ce profil</p>
          </div>
        )}
      </div>

      <div className="glass-card p-5 space-y-4">
        <div className="flex gap-2 flex-wrap">
          {domains.map(d => (
            <button
              key={d}
              onClick={() => { setDomainFilter(d); setRecommendation(null); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                domainFilter === d
                  ? 'bg-skills/30 text-skills border border-skills/40'
                  : 'bg-white/5 text-white/50 hover:bg-white/10 border border-white/10'
              }`}
            >
              {d || 'Tous domaines'}
            </button>
          ))}
        </div>

        {!selectedChallenge && (
          <div className="grid gap-3 md:grid-cols-2">
            {challenges.map(c => (
              <button
                key={c.id}
                onClick={() => selectChallenge(c.id)}
                className="text-left rounded-xl border border-white/10 bg-white/5 p-4 hover:bg-white/10 transition"
              >
                <p className="text-sm font-semibold text-white">{c.title}</p>
                <p className="text-xs text-white/40 mt-1">{c.domain} · {c.difficulty} · {c.estimated_time_minutes}min</p>
              </button>
            ))}
          </div>
        )}

        {selectedChallenge && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-white">{selectedChallenge.title}</p>
                <p className="text-xs text-white/40">{selectedChallenge.domain} · {selectedChallenge.difficulty}</p>
              </div>
              <button onClick={() => setSelectedChallenge(null)} className="text-xs text-white/50 hover:text-white">
                ← Retour à la liste
              </button>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/20 p-4">
              <p className="text-sm text-white/80 whitespace-pre-wrap">{selectedChallenge.statement}</p>
            </div>
            {selectedChallenge.test_cases?.map((tc: any, idx: number) => (
              <div key={tc.name} className="space-y-2">
                <p className="text-xs text-white/50 uppercase tracking-wider">
                  Q{idx + 1}: {tc.question}
                </p>
                <textarea
                  value={answers[tc.name] || ''}
                  onChange={(e) => setAnswers(prev => ({ ...prev, [tc.name]: e.target.value }))}
                  className="w-full min-h-[80px] rounded-xl border border-white/15 bg-black/20 p-3 text-sm text-white/90"
                  rows={3}
                  placeholder="Votre réponse..."
                />
              </div>
            ))}
            <TestButton onClick={runTest} loading={loading} label="Submit & Score Challenge" />
          </div>
        )}
      </div>

      <ResultCard result={result} title="Skills — Practical Challenge Result" />
    </div>
  );
}
