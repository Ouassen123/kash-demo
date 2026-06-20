'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';

import {
  startAbilitiesAssessment,
  submitAbilitiesAnswer,
  uploadKnowledgeCv,
  fetchCodingChallenges,
  submitCodingChallenge,
  saveInterviewAnswers,
  generateIntelligenceAssessment,
} from '@/lib/api';
import type { AbilitiesAssessmentQuestion, SubmitAbilitiesAnswerResponse } from '@/lib/types';

const interviewQuestions = [
  'Présente ton objectif académique ou professionnel principal.',
  'Décris un défi que tu as résolu et ce que tu as appris.',
  'Quelles compétences veux-tu améliorer dans les 3 prochains mois ?',
];

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
  const [skillsAssessmentId, setSkillsAssessmentId] = useState<string | null>(null);

  const [cvFile, setCvFile] = useState<File | null>(null);

  const [interviewAnswers, setInterviewAnswers] = useState<string[]>(Array(interviewQuestions.length).fill(''));
  const [cameraError, setCameraError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

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

  const completedCount = [abilitiesDone, knowledgeDone, interviewDone, skillsDone].filter(Boolean).length;
  const allDone = completedCount === 4;

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
          const tpl = defaultChallenge.templates?.[language] ?? defaultChallenge.templates?.python ?? '';
          setCode(tpl);
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
    const c = challenges.find((x: any) => x.id === challengeId);
    if (!c) return;
    const tpl = c.templates?.[language] ?? c.templates?.python ?? '';
    setCode(tpl);
    setChallengeResult(null);
  }, [challengeId, language]);

  async function enableCamera() {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      setCameraError(err instanceof Error ? err.message : 'Impossible d’accéder à la webcam');
    }
  }

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

  const interviewReady = useMemo(
    () => interviewAnswers.every((answer) => answer.trim().length >= 10),
    [interviewAnswers]
  );

  return (
    <section className="glass-panel p-6 space-y-6">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-mist/70">KASH full journey</p>
          <h1 className="text-2xl font-semibold text-white mt-2">Passer les 4 tests avant le résultat final</h1>
          <p className="text-sm text-white/70 mt-2">
            Ordre recommandé: Abilities test → Upload CV (Knowledge) → Entretien webcam → Upload code (Skills) → Résultat.
          </p>
        </div>
        <span className="rounded-full border border-white/20 bg-white/5 px-4 py-1 text-xs text-white/80">
          {completedCount}/4 complétés
        </span>
      </div>

      <article className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-3">
        <p className="text-sm font-semibold text-white">1) Abilities test (questions adaptatives)</p>

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

      <article ref={knowledgeSectionRef} className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-3">
        <p className="text-sm font-semibold text-white">2) Upload CV (Knowledge)</p>
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
            <div className="rounded-xl bg-emerald-500/10 border border-emerald-300/30 p-3 space-y-1">
              <p className="text-sm text-emerald-200 font-medium">
                ✓ CV analysé — Score global : {knowledgeScore !== null ? `${Math.round(knowledgeScore)}/100` : 'N/A'}
              </p>
              <p className="text-xs text-white/50">
                Pipeline : Data Cleaning → NLTK Tokenization → Stemming → TF-IDF → KNN Similarity
              </p>
            </div>
          )}
        </form>
      </article>

      <article className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-3">
        <p className="text-sm font-semibold text-white">3) Entretien webcam + réponses</p>
        <div className="flex items-center gap-3 flex-wrap">
          <button
            type="button"
            onClick={enableCamera}
            className="inline-flex rounded-full border border-white/20 px-4 py-2 text-xs text-white/80 hover:bg-white/10"
          >
            Activer webcam
          </button>
          {cameraError && <span className="text-rose-300 text-xs">{cameraError}</span>}
        </div>
        <video ref={videoRef} autoPlay muted playsInline className="w-full max-w-sm rounded-xl border border-white/10 bg-black/40" />
        <div className="space-y-3">
          {interviewQuestions.map((question, idx) => (
            <label key={question} className="block text-xs text-white/80 space-y-1">
              <span>{question}</span>
              <textarea
                value={interviewAnswers[idx]}
                onChange={(e) => {
                  const next = [...interviewAnswers];
                  next[idx] = e.target.value;
                  setInterviewAnswers(next);
                }}
                className="w-full rounded-xl border border-white/15 bg-white/5 p-2 text-sm"
                rows={3}
              />
            </label>
          ))}
        </div>
        {!interviewReady && (
          <p className="text-xs text-yellow-400/80">Réponds à toutes les questions (min. 10 caractères chacune) pour valider.</p>
        )}
        <button
          type="button"
          disabled={!interviewReady}
          onClick={async () => {
            setError(null);
            try {
              await saveInterviewAnswers({ answers: interviewAnswers });
              setInterviewDone(true);
            } catch (err) {
              setError(err instanceof Error ? err.message : 'Échec sauvegarde entretien');
            }
          }}
          className="inline-flex rounded-full bg-white text-midnight px-4 py-2 text-xs font-semibold hover:bg-mist transition disabled:opacity-60"
        >
          Valider entretien
        </button>
        {interviewDone && <span className="text-emerald-300 text-xs ml-3">Terminé</span>}
      </article>

      <article className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-3">
        <p className="text-sm font-semibold text-white">4) Upload projet/code (Skills)</p>
        <p className="text-xs text-white/60">
          Coding game : choisis un langage, écris ton code dans la page, puis on exécute des tests automatiques pour donner un score.
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
                <option value="java">Java</option>
              </select>
              {language === 'java' && (
                <p className="mt-1 text-[10px] text-amber-300/80">Java peut échouer si le compilateur n'est pas disponible sur le serveur.</p>
              )}
            </label>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={!code.trim() || submittingChallenge}
                className="inline-flex w-full justify-center rounded-full bg-white text-midnight px-4 py-2 text-xs font-semibold hover:bg-mist transition disabled:opacity-60"
              >
                {submittingChallenge ? 'Exécution...' : 'Exécuter & scorer'}
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
        <div className="rounded-2xl border border-emerald-300/40 bg-emerald-500/10 p-4">
          <p className="text-emerald-200 text-sm font-semibold">Les 4 étapes KASH sont complétées.</p>
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
            className="inline-flex mt-3 rounded-full bg-white text-midnight px-5 py-2 text-xs font-semibold hover:bg-mist transition disabled:opacity-60"
          >
            {generatingInsights ? 'Calcul du résultat...' : 'Voir le résultat global'}
          </button>
        </div>
      )}

      {error && <p className="text-sm text-rose-300">{error}</p>}
    </section>
  );
}
