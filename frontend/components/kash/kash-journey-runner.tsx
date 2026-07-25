'use client';

import Link from 'next/link';
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Brain, FileText, Video, Code, CheckCircle2, Circle, Loader2 } from 'lucide-react';

import {
  analyzeHabitsInterview,
  startAbilitiesAssessment,
  submitAbilitiesAnswer,
  uploadKnowledgeCv,
  fetchCodingChallenges,
  submitCodingChallenge,
  generateIntelligenceAssessment,
} from '@/lib/api';
import type {
  AbilitiesAssessmentQuestion,
  HabitsInterviewAnalysisResponse,
  HabitsInterviewAnswer,
  SubmitAbilitiesAnswerResponse,
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
  const [abilitiesDone, setAbilitiesDone] = useState(false);
  const [knowledgeDone, setKnowledgeDone] = useState(false);
  const [interviewDone, setInterviewDone] = useState(false);
  const [skillsDone, setSkillsDone] = useState(false);

  // ── Abilities quiz state ─────────────────────────────────────
  const [quizStarted, setQuizStarted] = useState(false);
  const [quizSessionId, setQuizSessionId] = useState<string | null>(null);
  const [quizAssessmentId, setQuizAssessmentId] = useState<string | null>(null);
  const [quizQuestion, setQuizQuestion] = useState<AbilitiesAssessmentQuestion | null>(null);
  const [quizIndex, setQuizIndex] = useState(0);
  const [quizTotal, setQuizTotal] = useState(0);
  const [quizAnswer, setQuizAnswer] = useState('');
  const [quizLastResult, setQuizLastResult] = useState<SubmitAbilitiesAnswerResponse | null>(null);
  const [quizLoading, setQuizLoading] = useState(false);
  const [quizError, setQuizError] = useState<string | null>(null);
  const [quizScore, setQuizScore] = useState<number | null>(null);
  const knowledgeSectionRef = useRef<HTMLElement | null>(null);
  const skillsSectionRef = useRef<HTMLElement | null>(null);

  // Auto-scroll to Knowledge section when abilities done
  useEffect(() => {
    if (abilitiesDone && knowledgeSectionRef.current) {
      setTimeout(() => knowledgeSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 300);
    }
  }, [abilitiesDone]);

  async function handleStartQuiz() {
    setQuizLoading(true);
    setQuizError(null);
    try {
      const res = await startAbilitiesAssessment({ quiz_type: 'cognitive', domain: 'memory', num_questions: 5, adaptive: true });
      setQuizSessionId(res.session_id);
      setQuizAssessmentId(res.assessment_id);
      setQuizQuestion(res.current_question);
      setQuizIndex(1);
      setQuizTotal(res.total_questions);
      setQuizStarted(true);
    } catch (e) {
      setQuizError(e instanceof Error ? e.message : 'Erreur démarrage quiz');
    } finally {
      setQuizLoading(false);
    }
  }

  async function handleSubmitQuizAnswer(e: FormEvent) {
    e.preventDefault();
    if (!quizSessionId || !quizQuestion || !quizAnswer) return;
    setQuizLoading(true);
    try {
      const res = await submitAbilitiesAnswer({
        session_id: quizSessionId,
        question_id: quizQuestion.id,
        answer: quizAnswer,
        response_time_ms: 3000,
      });
      setQuizLastResult(res);
      setQuizAnswer('');
      if (res.quiz_completed) {
        setQuizQuestion(null);
        setQuizScore(res.results?.percentage ?? null);
        setAbilitiesDone(true);
      } else {
        setQuizQuestion(res.next_question ?? null);
        setQuizIndex(res.question_number + 1);
      }
    } catch (e) {
      setQuizError(e instanceof Error ? e.message : 'Erreur soumission');
    } finally {
      setQuizLoading(false);
    }
  }

  const [knowledgeAssessmentId, setKnowledgeAssessmentId] = useState<string | null>(null);
  const [knowledgeScore, setKnowledgeScore] = useState<number | null>(null);
  const [knowledgeSkills, setKnowledgeSkills] = useState<string[]>([]);
  const [skillsAssessmentId, setSkillsAssessmentId] = useState<string | null>(null);

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
  const [interviewCaptureComplete, setInterviewCaptureComplete] = useState(false);

  const [loadingStep, setLoadingStep] = useState<'knowledge' | 'skills' | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ── Coding game state (Skills step) ─────────────────────────
  const [challengesLoading, setChallengesLoading] = useState(false);
  const [challenges, setChallenges] = useState<any[]>([]);
  const [challengeId, setChallengeId] = useState<string>('balanced-brackets-v1');
  const [language, setLanguage] = useState<'python' | 'java' | 'cpp'>('python');
  const [code, setCode] = useState<string>('');
  const [challengeResult, setChallengeResult] = useState<any | null>(null);
  const [submittingChallenge, setSubmittingChallenge] = useState(false);

  const [generatingInsights, setGeneratingInsights] = useState(false);

  const currentInterviewQuestion = interviewQuestions[currentInterviewIndex] ?? null;
  const currentInterviewResponse = interviewResponses[currentInterviewIndex] ?? null;
  const completedCount = [abilitiesDone, knowledgeDone, interviewDone, skillsDone].filter(Boolean).length;
  const allDone = completedCount === 4;

  const interviewReady = useMemo(() => {
    if (!currentInterviewResponse) return false;
    return currentInterviewResponse.answer_text.trim().length >= 10 && interviewCaptureComplete;
  }, [currentInterviewResponse, interviewCaptureComplete]);

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
    updateCurrentInterviewResponse({
      audio_base64: audioBase64,
      video_frames_base64: videoFramesBase64,
    });
    setInterviewCaptureComplete(true);
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
      const audioSegments = interviewResponses.map((response) => response.audio_base64 ?? '').filter(Boolean);
      const videoFramesBase64 = interviewResponses
        .flatMap((response) => response.video_frames_base64)
        .slice(-30);
      const audio_base64 = await mergeAudioBase64SegmentsToBase64(audioSegments);

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
  }, [interviewResponses]);

  const handleNextInterviewQuestion = useCallback(async () => {
    if (!currentInterviewResponse || !currentInterviewQuestion) return;
    if (!interviewReady) return;

    if (currentInterviewIndex < interviewQuestions.length - 1) {
      setCurrentInterviewIndex((value) => value + 1);
      setInterviewCaptureComplete(false);
      return;
    }

    await submitHabitsInterview();
  }, [currentInterviewIndex, currentInterviewQuestion, currentInterviewResponse, interviewReady, submitHabitsInterview]);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setChallengesLoading(true);
      try {
        const list = await fetchCodingChallenges();
        if (!mounted) return;
        setChallenges(list as any[]);
        const defaultChallenge = (list as any[]).find((c) => c.id === 'balanced-brackets-v1') ?? (list as any[])[0];
        if (defaultChallenge) {
          setChallengeId(defaultChallenge.id);
        }
      } catch (e) {
        // Don't block journey if challenge list fails.
      } finally {
        if (mounted) setChallengesLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    setChallengeResult(null);
  }, [challengeId, language]);

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
      setKnowledgeDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Échec upload CV');
    } finally {
      setLoadingStep(null);
    }
  }

  async function handleSubmitCodingChallenge(e: FormEvent) {
    e.preventDefault();
    if (!code.trim()) return;

    setSubmittingChallenge(true);
    setError(null);
    try {
      const res = await submitCodingChallenge({ challenge_id: challengeId, language, code });
      setChallengeResult(res);
      setSkillsAssessmentId(res.assessment_id);
      if (res.passed === res.total) {
        setSkillsDone(true);
      } else {
        setSkillsDone(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Échec soumission code');
    } finally {
      setSubmittingChallenge(false);
    }
  }

  return (
    <section className="glass-panel p-6 space-y-6 animate-fade-in">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-mist/70">KASH full journey</p>
          <h1 className="text-2xl font-bold text-white mt-2">Passer les 4 tests avant le résultat final</h1>
          <p className="text-sm text-white/70 mt-2">
            Ordre recommandé: Abilities test → Upload CV (Knowledge) → Entretien webcam → Upload code (Skills) → Résultat.
          </p>
        </div>
        <span className="rounded-full border border-white/20 bg-white/5 px-4 py-1 text-xs text-white/80">
          {completedCount}/4 complétés
        </span>
      </div>

      {/* Progress bar */}
      <div className="flex items-center gap-2">
        {[
          { label: 'Abilities', done: abilitiesDone, icon: Brain, color: 'text-abilities' },
          { label: 'Knowledge', done: knowledgeDone, icon: FileText, color: 'text-knowledge' },
          { label: 'Entretien', done: interviewDone, icon: Video, color: 'text-habits' },
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

      <article className={`rounded-2xl border p-5 space-y-3 transition-all ${abilitiesDone ? 'border-emerald-400/20 bg-emerald-500/5' : 'border-abilities/20 bg-abilities/5'}`}>
        <div className="flex items-center gap-3">
          <div className={`step-dot h-8 w-8 ${abilitiesDone ? 'step-dot-done' : 'step-dot-active'}`}>
            {abilitiesDone ? '✓' : '1'}
          </div>
          <p className="text-sm font-bold text-white">Abilities test (questions adaptatives)</p>
        </div>

        {/* Completed state */}
        {abilitiesDone && (
          <div className="rounded-xl bg-emerald-500/10 border border-emerald-300/30 p-3 text-sm text-emerald-200">
            ✓ Quiz terminé — Score&nbsp;: {quizScore !== null ? `${Math.round(quizScore)}%` : 'N/A'}
          </div>
        )}

        {/* Not started */}
        {!quizStarted && !abilitiesDone && (
          <>
            <p className="text-xs text-white/60">5 questions adaptatives sur le domaine Mémoire.</p>
            <button
              type="button"
              onClick={handleStartQuiz}
              disabled={quizLoading}
              className="inline-flex rounded-full bg-white text-midnight px-4 py-2 text-xs font-semibold hover:bg-mist transition disabled:opacity-60"
            >
              {quizLoading ? 'Démarrage...' : 'Commencer le test'}
            </button>
            {quizError && <p className="text-xs text-rose-300">{quizError}</p>}
          </>
        )}

        {/* Quiz in progress */}
        {quizStarted && !abilitiesDone && quizQuestion && (
          <form onSubmit={handleSubmitQuizAnswer} className="space-y-3">
            <p className="text-xs text-white/50 uppercase tracking-widest">Question {quizIndex} / {quizTotal}</p>
            <p className="text-sm text-white font-medium">{quizQuestion.question_text}</p>
            <div className="space-y-2">
              {quizQuestion.options.map((opt) => (
                <label key={opt} className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs cursor-pointer">
                  <input type="radio" name="quiz-ans" value={opt} checked={quizAnswer === opt} onChange={() => setQuizAnswer(opt)} />
                  <span>{opt}</span>
                </label>
              ))}
            </div>
            {quizLastResult && !quizLastResult.quiz_completed && (
              <p className="text-xs text-white/50">
                Dernière réponse : {quizLastResult.is_correct ? '✓ correcte' : '✗ incorrecte'}
              </p>
            )}
            <button
              type="submit"
              disabled={!quizAnswer || quizLoading}
              className="inline-flex rounded-full bg-white text-midnight px-4 py-2 text-xs font-semibold hover:bg-mist transition disabled:opacity-60"
            >
              {quizLoading ? 'Envoi...' : 'Valider'}
            </button>
            {quizError && <p className="text-xs text-rose-300">{quizError}</p>}
          </form>
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
            <div className="rounded-xl bg-emerald-500/10 border border-emerald-300/30 p-3 space-y-2">
              <p className="text-sm text-emerald-200 font-medium">
                ✓ CV analysé — Score global : {knowledgeScore !== null ? `${Math.round(knowledgeScore)}/100` : 'N/A'}
              </p>
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
              <p className="text-sm font-bold text-white">Entretien multimodal</p>
              <p className="text-xs text-white/60">Questions séquentielles avec capture audio/vidéo par question.</p>
            </div>
          </div>
          <span className="rounded-full border border-white/20 bg-white/5 px-3 py-1 text-[11px] text-white/70">
            {currentInterviewIndex + 1}/{interviewQuestions.length}
          </span>
        </div>

        {interviewAnalysisLoading && (
          <div className="rounded-2xl border border-cyan-300/30 bg-cyan-500/10 p-4 text-sm text-cyan-100">
            Analyse multimodale en cours...
          </div>
        )}

        {!interviewAnalysisLoading && currentInterviewQuestion && currentInterviewResponse && !interviewDone && (
          <div className="space-y-4 rounded-2xl border border-white/10 bg-black/20 p-4">
            <div className="space-y-2">
              <p className="text-xs uppercase tracking-widest text-white/40">
                Question {currentInterviewIndex + 1} / {interviewQuestions.length}
              </p>
              <p className="text-sm font-medium text-white">{currentInterviewQuestion.question_text}</p>
            </div>

            <label className="block space-y-2 text-xs text-white/70">
              <span>Réponse textuelle</span>
              <textarea
                value={currentInterviewResponse.answer_text}
                onChange={(e) => {
                  updateCurrentInterviewResponse({ answer_text: e.target.value });
                }}
                className="w-full rounded-2xl border border-white/15 bg-white/5 p-3 text-sm text-white outline-none transition focus:border-cyan-300/50"
                rows={4}
                placeholder="Tape ta réponse ou utilise cette zone comme transcription..."
              />
            </label>

            <WebcamAudioRecorder
              key={currentInterviewQuestion.id}
              title={`Capture média — question ${currentInterviewIndex + 1}`}
              onCaptureComplete={handleInterviewCaptureComplete}
            />

            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div className="text-xs text-white/60">
                {currentInterviewResponse.audio_base64 ? 'Audio capturé' : 'Audio en attente'}
                {currentInterviewResponse.video_frames_base64.length > 0 ? ` • ${currentInterviewResponse.video_frames_base64.length} frames` : ''}
              </div>
              <button
                type="button"
                onClick={handleNextInterviewQuestion}
                disabled={!interviewReady}
                className="inline-flex rounded-full bg-white text-midnight px-4 py-2 text-xs font-semibold hover:bg-mist transition disabled:opacity-60"
              >
                {currentInterviewIndex < interviewQuestions.length - 1 ? 'Question suivante' : 'Analyser l’entretien'}
              </button>
            </div>

            {!interviewReady && (
              <p className="text-xs text-yellow-300/80">
                Renseigne une réponse et termine la capture média pour passer à la question suivante.
              </p>
            )}
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
          <p className="text-sm font-bold text-white">Upload projet/code (Skills)</p>
        </div>
        <p className="text-xs text-white/60 ml-11">
          Coding game : choisis un challenge, un langage, écris ton code, puis on exécute des tests automatiques pour donner un score.
        </p>

        <form className="space-y-3" onSubmit={handleSubmitCodingChallenge}>
          <div className="grid gap-3 md:grid-cols-3">
            <label className="block text-xs text-white/70">
              Challenge
              <select
                value={challengeId}
                onChange={(e) => setChallengeId(e.target.value)}
                className="mt-1 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm"
                disabled={challengesLoading}
              >
                {challenges.map((c: any) => (
                  <option key={c.id} value={c.id}>{c.title}</option>
                ))}
              </select>
            </label>
            <label className="block text-xs text-white/70">
              Langage
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as any)}
                className="mt-1 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm"
              >
                <option value="python">Python</option>
                <option value="cpp">C++</option>
                <option value="javascript">JavaScript</option>
                <option value="java">Java</option>
              </select>
              {language === 'java' && (
                <p className="mt-1 text-[10px] text-amber-300/80">Java peut échouer si le compilateur n'est pas disponible sur le serveur.</p>
              )}
            </label>
            <div className="flex items-end gap-2">
              <button
                type="submit"
                disabled={!code.trim() || submittingChallenge}
                className="inline-flex flex-1 justify-center rounded-full bg-white text-midnight px-4 py-2 text-xs font-semibold hover:bg-mist transition disabled:opacity-60"
              >
                {submittingChallenge ? 'Exécution...' : 'Exécuter & scorer'}
              </button>
              <button
                type="button"
                onClick={() => {
                  const ch = challenges.find((c: any) => c.id === challengeId) as any;
                  if (ch?.templates?.[language]) setCode(ch.templates[language]);
                }}
                className="inline-flex justify-center rounded-full border border-white/20 px-3 py-2 text-xs text-white/80 hover:bg-white/10 transition"
              >
                Template
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-2">
            <p className="text-xs uppercase tracking-widest text-white/40">Énoncé</p>
            <pre className="whitespace-pre-wrap text-xs text-white/70">{(challenges.find((c: any) => c.id === challengeId) as any)?.statement ?? ''}</pre>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-white/10 bg-black/20 p-3">
                <p className="text-[10px] uppercase tracking-widest text-white/40">Sample input</p>
                <pre className="text-xs text-white/70 mt-1">{(challenges.find((c: any) => c.id === challengeId) as any)?.sample_input ?? ''}</pre>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/20 p-3">
                <p className="text-[10px] uppercase tracking-widest text-white/40">Sample output</p>
                <pre className="text-xs text-white/70 mt-1">{(challenges.find((c: any) => c.id === challengeId) as any)?.sample_output ?? ''}</pre>
              </div>
            </div>
          </div>

          <label className="block text-xs text-white/70">
            Code
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="mt-1 w-full min-h-[260px] rounded-xl border border-white/15 bg-black/30 p-3 font-mono text-xs text-white/80"
              spellCheck={false}
            />
          </label>

          {challengeResult && (
            <div className={`rounded-2xl border p-4 ${challengeResult.passed === challengeResult.total ? 'border-emerald-300/40 bg-emerald-500/10' : 'border-amber-300/40 bg-amber-500/10'}`}>
              <p className="text-sm font-semibold text-white">
                Score : {Math.round(challengeResult.score)}% — Tests : {challengeResult.passed}/{challengeResult.total}
              </p>
              {challengeResult.compile_output && (
                <pre className="mt-2 whitespace-pre-wrap text-xs text-white/70">{challengeResult.compile_output}</pre>
              )}
              <div className="mt-3 space-y-2">
                {Array.isArray(challengeResult.tests) && challengeResult.tests.slice(0, 6).map((t: any) => (
                  <div key={t.name} className="rounded-xl border border-white/10 bg-white/5 p-3">
                    <p className="text-xs text-white/80 font-medium">{t.passed ? '✓' : '✗'} {t.name} <span className="text-white/40">({t.runtime_ms} ms)</span></p>
                    {!t.passed && (
                      <div className="mt-2 grid gap-2 md:grid-cols-2">
                        <div>
                          <p className="text-[10px] uppercase tracking-widest text-white/40">Expected</p>
                          <pre className="text-xs text-white/70 whitespace-pre-wrap">{t.expected}</pre>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase tracking-widest text-white/40">Actual</p>
                          <pre className="text-xs text-white/70 whitespace-pre-wrap">{t.actual}</pre>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {skillsDone && <span className="text-emerald-300 text-xs">Terminé ({skillsAssessmentId})</span>}
          {!skillsDone && challengeResult && (
            <span className="text-amber-200 text-xs">Corrige ton code pour passer tous les tests et valider l'étape.</span>
          )}
        </form>
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
