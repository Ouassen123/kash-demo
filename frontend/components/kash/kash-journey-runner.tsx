'use client';

import Link from 'next/link';
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Brain, FileText, Video, Code, CheckCircle2, Circle, Loader2 } from 'lucide-react';

import {
  analyzeHabitsInterview,
  uploadKnowledgeCv,
  generateIntelligenceAssessment,
  API_BASE_URL,
} from '@/lib/api';
import type {
  HabitsInterviewAnalysisResponse,
  HabitsInterviewAnswer,
} from '@/lib/types';
import { WebcamAudioRecorder } from './WebcamAudioRecorder';
import { HabitsResultsView } from './HabitsResultsView';

const interviewQuestions = [
  { id: 'q1', question_text: 'Présente ton objectif académique ou professionnel principal.' },
  { id: 'q2', question_text: 'Décris un défi que tu as résolu et ce que tu as appris.' },
  { id: 'q3', question_text: 'Quelles compétences veux-tu améliorer dans les 3 prochains mois ?' },
];

type InterviewQuestionState = HabitsInterviewAnswer & {
  audio_base64: string | null;
  video_frames_base64: string[];
};

function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary = window.atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

function encodeWavFromMonoSamples(samples: Float32Array, sampleRate: number): ArrayBuffer {
  const bytesPerSample = 2;
  const buffer = new ArrayBuffer(44 + samples.length * bytesPerSample);
  const view = new DataView(buffer);

  const writeString = (offset: number, value: string) => {
    for (let i = 0; i < value.length; i += 1) {
      view.setUint8(offset + i, value.charCodeAt(i));
    }
  };

  writeString(0, 'RIFF');
  view.setUint32(4, 36 + samples.length * bytesPerSample, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * bytesPerSample, true);
  view.setUint16(32, bytesPerSample, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, samples.length * bytesPerSample, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i += 1) {
    const clamped = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true);
    offset += 2;
  }

  return buffer;
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }
  return window.btoa(binary);
}

async function mergeAudioBase64SegmentsToBase64(segments: string[]): Promise<string> {
  const usableSegments = segments.filter(Boolean);
  if (usableSegments.length === 0) return '';
  if (usableSegments.length === 1) return usableSegments[0];

  const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioContextClass) {
    return usableSegments[usableSegments.length - 1];
  }

  const audioContext = new AudioContextClass();
  try {
    const decodedBuffers = await Promise.all(
      usableSegments.map(async (segment) => {
        const buffer = base64ToArrayBuffer(segment);
        return audioContext.decodeAudioData(buffer.slice(0));
      })
    );

    const sampleRate = decodedBuffers[0].sampleRate;
    const mergedLength = decodedBuffers.reduce((total, buffer) => total + buffer.length, 0);
    const mergedSamples = new Float32Array(mergedLength);

    let offset = 0;
    decodedBuffers.forEach((buffer) => {
      mergedSamples.set(buffer.getChannelData(0), offset);
      offset += buffer.length;
    });

    const wavBuffer = encodeWavFromMonoSamples(mergedSamples, sampleRate);
    return arrayBufferToBase64(wavBuffer);
  } catch {
    return usableSegments[usableSegments.length - 1];
  } finally {
    if (typeof audioContext.close === 'function') {
      await audioContext.close().catch(() => undefined);
    }
  }
}

export function KashJourneyRunner() {
  // ── Step state ──────────────────────────────────────────────
  const [attitudeDone, setAttitudeDone] = useState(false);
  const [knowledgeDone, setKnowledgeDone] = useState(false);
  const [interviewDone, setInterviewDone] = useState(false);
  const [skillsDone, setSkillsDone] = useState(false);
  const [psyQuestions, setPsyQuestions] = useState<any[]>([]);
  const [psyAnswers, setPsyAnswers] = useState<Record<string, number>>({});
  const [psyLoading, setPsyLoading] = useState(true);
  const [psySubmitting, setPsySubmitting] = useState(false);
  const [psyResult, setPsyResult] = useState<any | null>(null);
  const [psyError, setPsyError] = useState<string | null>(null);

  const knowledgeSectionRef = useRef<HTMLElement | null>(null);
  const skillsSectionRef = useRef<HTMLElement | null>(null);

  const loadPsychometricQuestions = useCallback(async () => {
    setPsyLoading(true);
    setPsyError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/habits/psychometric/questions`);
      if (!res.ok) {
        throw new Error(`Erreur chargement questionnaire Likert (${res.status})`);
      }
      const questions = await res.json();
      setPsyQuestions(Array.isArray(questions) ? questions : []);
    } catch (err) {
      setPsyError(err instanceof Error ? err.message : 'Erreur chargement questionnaire Likert');
    } finally {
      setPsyLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPsychometricQuestions();
  }, [loadPsychometricQuestions]);

  // Auto-scroll to Knowledge section when abilities done
  useEffect(() => {
    if (attitudeDone && knowledgeSectionRef.current) {
      setTimeout(() => knowledgeSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 300);
    }
  }, [attitudeDone]);

  async function handleSubmitPsychometric(e: FormEvent) {
    e.preventDefault();
    const answered = Object.keys(psyAnswers).length;
    if (answered < psyQuestions.length) {
      setPsyError(`Il faut répondre aux ${psyQuestions.length} questions Likert (${answered}/${psyQuestions.length} répondues)`);
      return;
    }
    setPsySubmitting(true);
    setPsyError(null);
    try {
      const responses = Object.entries(psyAnswers).map(([qid, answer]) => ({ question_id: qid, answer }));
      const res = await fetch(`${API_BASE_URL}/habits/psychometric/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ responses }),
      });
      const data = await res.json();
      if (res.ok) {
        setPsyResult(data);
        setAttitudeDone(true);
      } else {
        setPsyError(data.detail ?? 'Erreur soumission psychometric');
      }
    } catch (err) {
      setPsyError(err instanceof Error ? err.message : 'Erreur soumission psychometric');
    } finally {
      setPsySubmitting(false);
    }
  }

  const [knowledgeAssessmentId, setKnowledgeAssessmentId] = useState<string | null>(null);
  const [knowledgeScore, setKnowledgeScore] = useState<number | null>(null);
  const [knowledgeSkills, setKnowledgeSkills] = useState<string[]>([]);
  const [knowledgeFiliere, setKnowledgeFiliere] = useState<string | null>(null);
  const [knowledgeTechDomains, setKnowledgeTechDomains] = useState<Record<string, number>>({});

  const [cvFile, setCvFile] = useState<File | null>(null);

  const [interviewResponses, setInterviewResponses] = useState<InterviewQuestionState[]>(() =>
    interviewQuestions.map((question) => ({
      question_id: question.id,
      question_text: question.question_text,
      answer_text: '',
      audio_base64: null,
      video_frames_base64: [],
    }))
  );
  const [currentInterviewIndex, setCurrentInterviewIndex] = useState(0);
  const [interviewAnalysis, setInterviewAnalysis] = useState<HabitsInterviewAnalysisResponse | null>(null);
  const [interviewAnalysisLoading, setInterviewAnalysisLoading] = useState(false);

  // Continuous recording: single recorder for all questions
  const [continuousAudioSegments, setContinuousAudioSegments] = useState<string[]>([]);
  const [continuousVideoFrames, setContinuousVideoFrames] = useState<string[]>([]);
  const [isRecordingActive, setIsRecordingActive] = useState(false);

  const [loadingStep, setLoadingStep] = useState<'knowledge' | 'skills' | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ── Practical challenges state (Skills step — domain-adaptive) ────
  const [practicalChallenges, setPracticalChallenges] = useState<any[]>([]);
  const [selectedPracticalChallenge, setSelectedPracticalChallenge] = useState<any | null>(null);
  const [practicalAnswers, setPracticalAnswers] = useState<Record<string, string>>({});
  const [practicalResult, setPracticalResult] = useState<any | null>(null);
  const [practicalLoading, setPracticalLoading] = useState(false);

  const [generatingInsights, setGeneratingInsights] = useState(false);

  const currentInterviewQuestion = interviewQuestions[currentInterviewIndex] ?? null;
  const currentInterviewResponse = interviewResponses[currentInterviewIndex] ?? null;
  const completedCount = [attitudeDone, knowledgeDone, interviewDone, skillsDone].filter(Boolean).length;
  const allDone = completedCount === 4;

  const interviewReady = useMemo(() => {
    if (!currentInterviewResponse) return false;
    // Ready if text answer is long enough OR audio was captured
    return currentInterviewResponse.answer_text.trim().length >= 10 || (currentInterviewResponse.audio_base64 !== null);
  }, [currentInterviewResponse]);

  const updateCurrentInterviewResponse = useCallback((patch: Partial<InterviewQuestionState>) => {
    setInterviewResponses((previous) =>
      previous.map((item, index) =>
        index === currentInterviewIndex
          ? {
              ...item,
              ...patch,
            }
          : item
      )
    );
  }, [currentInterviewIndex]);

  const handleInterviewCaptureComplete = useCallback((audioBase64: string, videoFramesBase64: string[]) => {
    // Accumulate segments for continuous recording
    setContinuousAudioSegments((prev) => audioBase64 ? [...prev, audioBase64] : prev);
    setContinuousVideoFrames((prev) => [...prev, ...videoFramesBase64]);
    updateCurrentInterviewResponse({
      audio_base64: audioBase64 || null,
      video_frames_base64: videoFramesBase64,
    });
    setIsRecordingActive(false);
  }, [updateCurrentInterviewResponse]);

  const submitHabitsInterview = useCallback(async () => {
    setInterviewAnalysisLoading(true);
    setError(null);
    try {
      const answers = interviewResponses.map((response) => ({
        question_id: response.question_id,
        question_text: response.question_text,
        answer_text: response.answer_text.trim(),
      }));
      // Use accumulated audio segments from continuous recording
      const audioSegments = continuousAudioSegments.filter(Boolean);
      const videoFramesBase64 = continuousVideoFrames.slice(-30);
      const audio_base64 = audioSegments.length > 0
        ? await mergeAudioBase64SegmentsToBase64(audioSegments)
        : '';

      const analysis = await analyzeHabitsInterview({
        answers,
        audio_base64,
        video_frames_base64: videoFramesBase64,
        industry: 'technology',
      });

      setInterviewAnalysis(analysis);
      setInterviewDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Échec analyse multimodale');
    } finally {
      setInterviewAnalysisLoading(false);
    }
  }, [interviewResponses, continuousAudioSegments, continuousVideoFrames]);

  const handleNextInterviewQuestion = useCallback(async () => {
    if (!currentInterviewResponse || !currentInterviewQuestion) return;
    if (!interviewReady) return;

    if (currentInterviewIndex < interviewQuestions.length - 1) {
      setCurrentInterviewIndex((value) => value + 1);
      return;
    }

    await submitHabitsInterview();
  }, [currentInterviewIndex, currentInterviewQuestion, currentInterviewResponse, interviewReady, submitHabitsInterview]);

  async function handleUploadCv(e: FormEvent) {
    e.preventDefault();
    if (!cvFile) return;

    setLoadingStep('knowledge');
    setError(null);
    try {
      const response = await uploadKnowledgeCv(cvFile);
      setKnowledgeAssessmentId(response.assessment_id);
      const ks = response.knowledge_scores ?? {};
      const score = ks.normalized_score ?? ks.overall ?? response.normalized_score ?? response.confidence_score ?? null;
      setKnowledgeScore(typeof score === 'number' ? score : null);
      const extractedSkills = (response.skills ?? [])
        .map((s: { name?: string } | string) => (typeof s === 'string' ? s : s.name))
        .filter((skill): skill is string => Boolean(skill));
      setKnowledgeSkills(extractedSkills);
      // Extract filiere and tech domains from knowledge scores
      setKnowledgeFiliere((ks.predicted_filiere as string) ?? null);
      setKnowledgeTechDomains((ks.detected_tech_domains as Record<string, number>) ?? {});
      setKnowledgeDone(true);

      // Auto-load practical challenges adapted to detected domain
      try {
        const domains = ks.detected_tech_domains ?? {};
        const topDomain = Object.entries(domains)
          .sort(([, a]: any, [, b]: any) => b - a)[0];

        let challengeDomain = '';
        if (topDomain) {
          const domainKey = topDomain[0];
          const domainMap: Record<string, string> = {
            electrical: 'electrical', mechanical: 'mechanical',
            quality: 'quality', logistics: 'logistics', management: 'management',
            software: 'management',
          };
          challengeDomain = domainMap[domainKey] ?? domainKey;
        }

        const challengesUrl = challengeDomain
          ? `${API_BASE_URL}/skills/practical/challenges?domain=${challengeDomain}`
          : `${API_BASE_URL}/skills/practical/challenges`;
        const token = typeof window !== 'undefined' ? localStorage.getItem('kash_token') : null;
        const res = await fetch(challengesUrl, {
          headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        });
        if (res.ok) {
          const challenges = await res.json();
          setPracticalChallenges(challenges);
          if (challenges.length > 0) {
            setSelectedPracticalChallenge(challenges[0]);
            const init: Record<string, string> = {};
            challenges[0].test_cases?.forEach((tc: any) => { init[tc.name] = ''; });
            setPracticalAnswers(init);
          }
        }
      } catch (e) {
        // Fallback: load all practical challenges
        try {
          const token2 = typeof window !== 'undefined' ? localStorage.getItem('kash_token') : null;
          const res = await fetch(`${API_BASE_URL}/skills/practical/challenges`, {
            headers: { ...(token2 ? { Authorization: `Bearer ${token2}` } : {}) },
          });
          if (res.ok) {
            const challenges = await res.json();
            setPracticalChallenges(challenges);
            if (challenges.length > 0) {
              setSelectedPracticalChallenge(challenges[0]);
              const init: Record<string, string> = {};
              challenges[0].test_cases?.forEach((tc: any) => { init[tc.name] = ''; });
              setPracticalAnswers(init);
            }
          }
        } catch {}
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Échec upload CV');
    } finally {
      setLoadingStep(null);
    }
  }

  async function handleSubmitPracticalChallenge(e: FormEvent) {
    e.preventDefault();
    if (!selectedPracticalChallenge) return;

    setPracticalLoading(true);
    setError(null);
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('kash_token') : null;
      const res = await fetch(`${API_BASE_URL}/skills/practical/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          challenge_id: selectedPracticalChallenge.id,
          answers: practicalAnswers,
        }),
      });
      const data = await res.json();
      setPracticalResult(data);
      if (data.passed === data.total) {
        setSkillsDone(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Échec soumission challenge');
    } finally {
      setPracticalLoading(false);
    }
  }

  return (
    <section className="glass-panel p-6 space-y-6 animate-fade-in">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-mist/70">KASH full journey</p>
          <h1 className="text-2xl font-bold text-white mt-2">Passer les 4 tests avant le résultat final</h1>
          <p className="text-sm text-white/70 mt-2">
            Ordre recommandé: Attitude test → Upload CV (Knowledge) → Entretien webcam → Upload code (Skills) → Résultat.
          </p>
        </div>
        <span className="rounded-full border border-white/20 bg-white/5 px-4 py-1 text-xs text-white/80">
          {completedCount}/4 complétés
        </span>
      </div>

      {/* Progress bar */}
      <div className="flex items-center gap-2">
        {[
          { label: 'Attitude', done: attitudeDone, icon: Brain, color: 'text-abilities' },
          { label: 'Knowledge', done: knowledgeDone, icon: FileText, color: 'text-knowledge' },
          { label: 'Habits', done: interviewDone, icon: Video, color: 'text-habits' },
          { label: 'Skills', done: skillsDone, icon: Code, color: 'text-skills' },
        ].map((step, i) => {
          const Icon = step.icon;
          return (
            <div key={step.label} className="flex items-center gap-2 flex-1">
              <div className={`flex items-center gap-2 rounded-xl px-3 py-2 border transition-all ${step.done ? 'border-emerald-400/30 bg-emerald-500/10' : 'border-white/10 bg-white/5'}`}>
                {step.done ? <CheckCircle2 size={18} className="text-emerald-400" /> : <Icon size={18} className={step.color} />}
                <span className={`text-xs font-medium ${step.done ? 'text-emerald-300' : 'text-white/70'}`}>{step.label}</span>
              </div>
              {i < 3 && <div className={`h-px flex-1 ${step.done ? 'bg-emerald-400/40' : 'bg-white/10'}`} />}
            </div>
          );
        })}
      </div>

      <article className={`rounded-2xl border p-5 space-y-3 transition-all ${attitudeDone ? 'border-emerald-400/20 bg-emerald-500/5' : 'border-abilities/20 bg-abilities/5'}`}>
        <div className="flex items-center gap-3">
          <div className={`step-dot h-8 w-8 ${attitudeDone ? 'step-dot-done' : 'step-dot-active'}`}>
            {attitudeDone ? '✓' : '1'}
          </div>
          <div>
            <p className="text-sm font-bold text-white">Attitude</p>
            <p className="text-xs text-white/50">20 questions Likert 1-5.</p>
          </div>
        </div>

        {attitudeDone && psyResult ? (
          <div className="rounded-xl bg-emerald-500/10 border border-emerald-300/30 p-3 space-y-2">
            <p className="text-sm text-emerald-200">
              ✓ Questionnaire Likert terminé — Score&nbsp;: {Math.round(psyResult.overall_habits_score)}/100 ({psyResult.discipline_level})
            </p>
            <p className="text-xs text-emerald-100/80">Tes réponses ont bien été enregistrées.</p>
          </div>
        ) : (
          <>
            {psyLoading ? (
              <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-xs text-white/60">
                Chargement des 20 questions Likert...
              </div>
            ) : psyError ? (
              <div className="rounded-xl border border-rose-400/30 bg-rose-500/10 p-3 space-y-2">
                <p className="text-xs text-rose-200">{psyError}</p>
                <button
                  type="button"
                  onClick={() => void loadPsychometricQuestions()}
                  className="inline-flex rounded-full bg-white text-midnight px-4 py-2 text-xs font-semibold hover:bg-mist transition"
                >
                  Réessayer
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmitPsychometric} className="space-y-4">
                <div className="rounded-xl bg-habits/10 border border-habits/30 p-3">
                  <p className="text-xs font-semibold text-habits">Habits</p>
                  <p className="text-xs text-white/50 mt-1">
                    Réponds honnêtement sur l'échelle 1-5.
                  </p>
                </div>
                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                  {psyQuestions.map((q, idx) => (
                    <div key={q.id} className="rounded-xl border border-white/10 bg-white/5 p-3 space-y-2">
                      <p className="text-xs text-white/80">
                        <span className="text-white/40">Q{idx + 1}.</span> {q.text}
                      </p>
                      <p className="text-[10px] text-white/30 uppercase tracking-wider">{q.dimension} · {q.subscale}</p>
                      <div className="flex gap-1.5 flex-wrap">
                        {q.scale.labels.map((label: string, i: number) => (
                          <label key={i} className={`flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] cursor-pointer border transition ${psyAnswers[q.id] === i + 1 ? 'border-habits/50 bg-habits/20 text-habits' : 'border-white/10 bg-white/5 text-white/60 hover:bg-white/10'}`}>
                            <input
                              type="radio"
                              name={`psy-${q.id}`}
                              value={i + 1}
                              checked={psyAnswers[q.id] === i + 1}
                              onChange={() => setPsyAnswers((prev) => ({ ...prev, [q.id]: i + 1 }))}
                              className="hidden"
                            />
                            <span>{i + 1}</span>
                            <span className="hidden sm:inline">{label}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="submit"
                    disabled={psySubmitting || psyQuestions.length === 0 || Object.keys(psyAnswers).length < psyQuestions.length}
                    className="inline-flex rounded-full bg-white text-midnight px-4 py-2 text-xs font-semibold hover:bg-mist transition disabled:opacity-60"
                  >
                    {psySubmitting ? 'Évaluation...' : `Soumettre (${Object.keys(psyAnswers).length}/${psyQuestions.length})`}
                  </button>
                  {psyError && <p className="text-xs text-rose-300">{psyError}</p>}
                </div>
              </form>
            )}
          </>
        )}
      </article>

      <article ref={knowledgeSectionRef} className={`rounded-2xl border p-5 space-y-3 transition-all ${knowledgeDone ? 'border-emerald-400/20 bg-emerald-500/5' : 'border-knowledge/20 bg-knowledge/5'}`}>
        <div className="flex items-center gap-3">
          <div className={`step-dot h-8 w-8 ${knowledgeDone ? 'step-dot-done' : 'step-dot-active'}`}>
            {knowledgeDone ? '✓' : '2'}
          </div>
          <p className="text-sm font-bold text-white">Upload CV (Knowledge)</p>
        </div>
        <form className="flex flex-wrap gap-3 items-center" onSubmit={handleUploadCv}>
          <input type="file" accept=".txt,.pdf,.docx" onChange={(e) => setCvFile(e.target.files?.[0] ?? null)} />
          <button
            type="submit"
            disabled={!cvFile || loadingStep === 'knowledge'}
            className="inline-flex rounded-full bg-white text-midnight px-4 py-2 text-xs font-semibold hover:bg-mist transition disabled:opacity-60"
          >
            {loadingStep === 'knowledge' ? 'Upload...' : 'Uploader CV'}
          </button>
          {knowledgeDone && (
            <div className="rounded-xl bg-emerald-500/10 border border-emerald-300/30 p-3 space-y-2 w-full">
              <p className="text-sm text-emerald-200 font-medium">
                ✓ CV analysé — Score global : {knowledgeScore !== null ? `${Math.round(knowledgeScore)}/100` : 'N/A'}
              </p>
              {knowledgeFiliere && (
                <div className="space-y-1">
                  <p className="text-xs text-white/60">Filière détectée :</p>
                  <p className="text-sm text-white font-bold">{knowledgeFiliere}</p>
                </div>
              )}
              {Object.keys(knowledgeTechDomains).length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs text-white/60">Domaines techniques :</p>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(knowledgeTechDomains).map(([domain, hits]) => (
                      <span key={domain} className="rounded-full bg-knowledge/15 px-2.5 py-0.5 text-xs text-knowledge">
                        {domain}: {hits}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              <p className="text-xs text-white/50">
                Pipeline : Data Cleaning → NLTK Tokenization → Stemming → TF-IDF → KNN Similarity
              </p>
              {knowledgeSkills.length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs text-white/60">Skills extraites ({knowledgeSkills.length}) :</p>
                  <div className="flex flex-wrap gap-1.5">
                    {knowledgeSkills.map((s) => (
                      <span key={s} className="rounded-full bg-aurora/15 px-2.5 py-0.5 text-xs text-aurora">{s}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </form>
      </article>

      <article className={`rounded-2xl border p-5 space-y-3 transition-all ${interviewDone ? 'border-emerald-400/20 bg-emerald-500/5' : 'border-habits/20 bg-habits/5'}`}>
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <div className={`step-dot h-8 w-8 ${interviewDone ? 'step-dot-done' : 'step-dot-active'}`}>
              {interviewDone ? '✓' : '3'}
            </div>
            <div>
              <p className="text-sm font-bold text-white">Habits — Entretien comportemental</p>
              <p className="text-xs text-white/60">Enregistrement continu. Réponds par texte, oral, ou les deux. La caméra reste active pendant tout l'entretien.</p>
            </div>
          </div>
          <span className="rounded-full border border-white/20 bg-white/5 px-3 py-1 text-[11px] text-white/70">
            {currentInterviewIndex + 1}/{interviewQuestions.length}
          </span>
        </div>

        {interviewAnalysisLoading && (
          <div className="rounded-2xl border border-cyan-300/30 bg-cyan-500/10 p-4 text-sm text-cyan-100">
            Analyse multimodale Habits en cours...
          </div>
        )}

        {!interviewAnalysisLoading && currentInterviewQuestion && currentInterviewResponse && !interviewDone && (
          <div className="space-y-4">
            {/* Continuous recorder — no key change, stays mounted */}
            <WebcamAudioRecorder
              key="continuous-habits-recorder"
              title="Habits — Enregistrement continu"
              onCaptureComplete={handleInterviewCaptureComplete}
            />

            {continuousAudioSegments.length > 0 && (
              <div className="rounded-xl bg-habits/10 border border-habits/30 p-2 text-xs text-habits">
                ✓ {continuousAudioSegments.length} segment(s) audio capturé(s) · {continuousVideoFrames.length} frames vidéo
              </div>
            )}

            <div className="space-y-4 rounded-2xl border border-white/10 bg-black/20 p-4">
              <div className="space-y-2">
                <p className="text-xs uppercase tracking-widest text-habits/60">
                  Question {currentInterviewIndex + 1} / {interviewQuestions.length}
                </p>
                <p className="text-sm font-medium text-white">{currentInterviewQuestion.question_text}</p>
              </div>

              <label className="block space-y-2 text-xs text-white/70">
                <span>Réponse (texte et/ou oral)</span>
                <textarea
                  value={currentInterviewResponse.answer_text}
                  onChange={(e) => {
                    updateCurrentInterviewResponse({ answer_text: e.target.value });
                  }}
                  className="w-full rounded-2xl border border-white/15 bg-white/5 p-3 text-sm text-white outline-none transition focus:border-habits/50"
                  rows={4}
                  placeholder="Tape ta réponse ici, ou réponds oralement avec le recorder ci-dessus, ou les deux..."
                />
              </label>

              <div className="flex items-center justify-between gap-3 flex-wrap">
                <div className="text-xs text-white/60">
                  {currentInterviewResponse.answer_text.trim().length > 0 && `Texte: ${currentInterviewResponse.answer_text.trim().length} chars`}
                  {currentInterviewResponse.audio_base64 && ' · Audio capturé'}
                </div>
                <button
                  type="button"
                  onClick={handleNextInterviewQuestion}
                  disabled={!interviewReady}
                  className="inline-flex rounded-full bg-white text-midnight px-4 py-2 text-xs font-semibold hover:bg-mist transition disabled:opacity-60"
                >
                  {currentInterviewIndex < interviewQuestions.length - 1 ? 'Question suivante' : "Analyser l'entretien"}
                </button>
              </div>

              {!interviewReady && (
                <p className="text-xs text-yellow-300/80">
                  Réponds par texte (min 10 caractères) ou par oral pour passer à la question suivante.
                </p>
              )}
            </div>
          </div>
        )}

        {interviewAnalysis && (
          <div className="space-y-4">
            <HabitsResultsView analysis={interviewAnalysis} />
            <div className="flex items-center justify-between gap-3 flex-wrap rounded-2xl border border-white/10 bg-white/5 p-4">
              <div>
                <p className="text-sm font-medium text-white">Entretien Habits terminé</p>
                <p className="text-xs text-white/60">Tu peux maintenant passer à l’étape Skills pour finaliser le test KASH.</p>
              </div>
              <button
                type="button"
                onClick={() => skillsSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                className="inline-flex rounded-full bg-white text-midnight px-4 py-2 text-xs font-semibold hover:bg-mist transition"
              >
                Continuer vers Skills
              </button>
            </div>
          </div>
        )}

        {interviewDone && <span className="text-emerald-300 text-xs">Terminé</span>}
      </article>

      <article ref={skillsSectionRef} className={`rounded-2xl border p-5 space-y-3 transition-all ${skillsDone ? 'border-emerald-400/20 bg-emerald-500/5' : 'border-skills/20 bg-skills/5'}`}>
        <div className="flex items-center gap-3">
          <div className={`step-dot h-8 w-8 ${skillsDone ? 'step-dot-done' : 'step-dot-active'}`}>
            {skillsDone ? '✓' : '4'}
          </div>
          <div>
            <p className="text-sm font-bold text-white">Practical Challenge (Skills)</p>
            {knowledgeFiliere && (
              <p className="text-xs text-skills/80">Adapté à ta filière : {knowledgeFiliere}</p>
            )}
          </div>
        </div>
        <p className="text-xs text-white/60 ml-11">
          Challenge pratique : réponds aux questions techniques liées à ton domaine. Le système évalue tes réponses avec scoring sémantique.
        </p>

        {!selectedPracticalChallenge && practicalChallenges.length === 0 && (
          <p className="text-xs text-white/50 ml-11">
            {knowledgeDone
              ? 'Chargement des challenges adaptés à ton domaine...'
              : 'Upload ton CV d\'abord (étape 2) pour recevoir un challenge adapté à ta filière.'}
          </p>
        )}

        {practicalChallenges.length > 0 && (
          <form className="space-y-3" onSubmit={handleSubmitPracticalChallenge}>
            {/* Challenge selector */}
            <label className="block text-xs text-white/70 ml-11">
              Challenge
              <select
                value={selectedPracticalChallenge?.id ?? ''}
                onChange={(e) => {
                  const ch = practicalChallenges.find((c: any) => c.id === e.target.value);
                  setSelectedPracticalChallenge(ch ?? null);
                  if (ch) {
                    const init: Record<string, string> = {};
                    ch.test_cases?.forEach((tc: any) => { init[tc.name] = ''; });
                    setPracticalAnswers(init);
                  }
                  setPracticalResult(null);
                }}
                className="mt-1 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm"
              >
                {practicalChallenges.map((c: any) => (
                  <option key={c.id} value={c.id}>{c.title} ({c.domain})</option>
                ))}
              </select>
            </label>

            {/* Challenge statement */}
            {selectedPracticalChallenge && (
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-2 ml-11">
                <p className="text-xs uppercase tracking-widest text-white/40">Énoncé</p>
                <pre className="whitespace-pre-wrap text-xs text-white/70">{selectedPracticalChallenge.statement}</pre>
                <p className="text-[10px] text-white/40">{selectedPracticalChallenge.domain} · {selectedPracticalChallenge.difficulty} · {selectedPracticalChallenge.estimated_time_minutes}min</p>
              </div>
            )}

            {/* Questions */}
            {selectedPracticalChallenge?.test_cases?.map((tc: any, idx: number) => (
              <div key={tc.name} className="space-y-2 ml-11">
                <p className="text-xs text-white/50 uppercase tracking-wider">
                  Q{idx + 1}: {tc.question}
                </p>
                <textarea
                  value={practicalAnswers[tc.name] ?? ''}
                  onChange={(e) => setPracticalAnswers((prev) => ({ ...prev, [tc.name]: e.target.value }))}
                  className="w-full min-h-[80px] rounded-xl border border-white/15 bg-black/20 p-3 text-sm text-white/90"
                  rows={3}
                  placeholder="Votre réponse..."
                />
              </div>
            ))}

            <div className="ml-11">
              <button
                type="submit"
                disabled={practicalLoading || !selectedPracticalChallenge}
                className="inline-flex rounded-full bg-white text-midnight px-4 py-2 text-xs font-semibold hover:bg-mist transition disabled:opacity-60"
              >
                {practicalLoading ? 'Évaluation...' : 'Soumettre & Évaluer'}
              </button>
            </div>

            {/* Results */}
            {practicalResult && (
              <div className={`rounded-2xl border p-4 ml-11 ${practicalResult.passed === practicalResult.total ? 'border-emerald-300/40 bg-emerald-500/10' : 'border-amber-300/40 bg-amber-500/10'}`}>
                <p className="text-sm font-semibold text-white">
                  Score : {Math.round(practicalResult.overall_score * 100)}% — Tests : {practicalResult.passed}/{practicalResult.total}
                </p>
                <p className="text-xs text-white/60 mt-1">{practicalResult.recommendation}</p>
                <div className="mt-3 space-y-2">
                  {Array.isArray(practicalResult.results) && practicalResult.results.map((r: any) => (
                    <div key={r.name} className="rounded-xl border border-white/10 bg-white/5 p-3">
                      <p className="text-xs text-white/80 font-medium">
                        {r.passed ? '✓' : '✗'} {r.name} <span className="text-white/40">({Math.round(r.score * 100)}%)</span>
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {skillsDone && <span className="text-emerald-300 text-xs ml-11">Terminé ✓</span>}
            {!skillsDone && practicalResult && practicalResult.passed < practicalResult.total && (
              <span className="text-amber-200 text-xs ml-11">Améliore tes réponses pour passer tous les tests.</span>
            )}
          </form>
        )}
      </article>

      {allDone && (
        <div className="rounded-2xl border border-emerald-300/40 bg-gradient-to-r from-emerald-500/15 to-aurora/10 p-5 animate-fade-in">
          <p className="text-emerald-200 text-sm font-bold">✓ Les 4 étapes KASH sont complétées.</p>
          <button
            type="button"
            onClick={async () => {
              setGeneratingInsights(true);
              setError(null);
              try {
                await generateIntelligenceAssessment({ industry: 'technology', career_goals: ['software_engineer'] });
                window.location.href = '/intelligence/insights';
              } catch (err) {
                setError(err instanceof Error ? err.message : 'Échec génération insights');
              } finally {
                setGeneratingInsights(false);
              }
            }}
            disabled={generatingInsights}
            className="btn-gradient mt-3 disabled:opacity-60"
          >
            {generatingInsights ? 'Calcul du résultat...' : 'Voir le résultat global'}
            <span aria-hidden>→</span>
          </button>
        </div>
      )}

      {error && <p className="text-sm text-rose-300">{error}</p>}
    </section>
  );
}
