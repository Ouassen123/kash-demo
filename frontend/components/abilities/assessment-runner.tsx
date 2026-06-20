'use client';

import { FormEvent, useMemo, useState } from 'react';

import { startAbilitiesAssessment, submitAbilitiesAnswer } from '@/lib/api';
import type { AbilitiesAssessmentQuestion, SubmitAbilitiesAnswerResponse } from '@/lib/types';

const domainOptions = [
  { value: 'memory', label: 'Memory' },
  { value: 'attention', label: 'Attention' },
  { value: 'processing_speed', label: 'Processing speed' },
  { value: 'executive_function', label: 'Executive function' },
  { value: 'language', label: 'Language' },
  { value: 'visual_spatial', label: 'Visual spatial' },
  { value: 'problem_solving', label: 'Problem solving' },
  { value: 'creativity', label: 'Creativity' },
] as const;

export function AbilitiesAssessmentRunner() {
  const [domain, setDomain] = useState<(typeof domainOptions)[number]['value']>('memory');
  const [numQuestions, setNumQuestions] = useState(10);
  const [adaptive, setAdaptive] = useState(true);

  const [assessmentId, setAssessmentId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState<AbilitiesAssessmentQuestion | null>(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);

  const [selectedAnswer, setSelectedAnswer] = useState<string>('');
  const [questionStartMs, setQuestionStartMs] = useState<number>(0);
  const [lastResult, setLastResult] = useState<SubmitAbilitiesAnswerResponse | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isRunning = !!sessionId && !!question;
  const isCompleted = !!sessionId && !question && !!lastResult?.quiz_completed;

  const progressPct = useMemo(() => {
    if (!totalQuestions) return 0;
    return Math.min(100, Math.round((questionIndex / totalQuestions) * 100));
  }, [questionIndex, totalQuestions]);

  async function handleStartAssessment(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setLastResult(null);

    try {
      const response = await startAbilitiesAssessment({
        quiz_type: 'cognitive',
        domain,
        num_questions: numQuestions,
        adaptive,
      });

      setAssessmentId(response.assessment_id);
      setSessionId(response.session_id);
      setQuestion(response.current_question);
      setQuestionIndex(response.question_number);
      setTotalQuestions(response.total_questions);
      setSelectedAnswer('');
      setQuestionStartMs(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Impossible de démarrer le test');
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmitAnswer(e: FormEvent) {
    e.preventDefault();
    if (!sessionId || !question || !selectedAnswer) return;

    setLoading(true);
    setError(null);

    try {
      const response = await submitAbilitiesAnswer({
        session_id: sessionId,
        question_id: question.id,
        answer: selectedAnswer,
        response_time_ms: Math.max(1, Date.now() - questionStartMs),
      });

      setLastResult(response);
      setQuestion(response.next_question ?? null);
      // question_number is the index of the answered question; next question is +1
      setQuestionIndex(response.quiz_completed ? totalQuestions : response.question_number + 1);
      setSelectedAnswer('');
      setQuestionStartMs(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Impossible de soumettre la réponse');
    } finally {
      setLoading(false);
    }
  }

  function resetRunner() {
    setAssessmentId(null);
    setSessionId(null);
    setQuestion(null);
    setQuestionIndex(0);
    setTotalQuestions(0);
    setSelectedAnswer('');
    setQuestionStartMs(0);
    setLastResult(null);
    setError(null);
  }

  return (
    <section className="glass-panel p-6 space-y-5">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Start assessment</p>
        <p className="text-2xl font-semibold mt-1 text-white">Lancer un test adaptatif</p>
        <p className="text-sm text-white/70 mt-2">
          Configure le domaine, lance le quiz, réponds aux questions, puis récupère le score final.
        </p>
      </div>

      {!sessionId && (
        <form className="grid gap-4 md:grid-cols-2" onSubmit={handleStartAssessment}>
          <label className="flex flex-col gap-2 text-sm text-white/80">
            Domaine
            <select
              className="rounded-xl bg-white/5 border border-white/15 px-3 py-2"
              value={domain}
              onChange={(e) => setDomain(e.target.value as (typeof domainOptions)[number]['value'])}
            >
              {domainOptions.map((option) => (
                <option key={option.value} value={option.value} className="text-black">
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-2 text-sm text-white/80">
            Nombre de questions (5-50)
            <input
              type="number"
              min={5}
              max={50}
              value={numQuestions}
              onChange={(e) => setNumQuestions(Number(e.target.value))}
              className="rounded-xl bg-white/5 border border-white/15 px-3 py-2"
            />
          </label>

          <label className="inline-flex items-center gap-2 text-sm text-white/80 md:col-span-2">
            <input type="checkbox" checked={adaptive} onChange={(e) => setAdaptive(e.target.checked)} />
            Mode adaptatif activé
          </label>

          <button
            type="submit"
            disabled={loading}
            className="md:col-span-2 inline-flex justify-center rounded-full bg-white text-midnight px-6 py-2 text-sm font-semibold hover:bg-mist transition disabled:opacity-60"
          >
            {loading ? 'Démarrage...' : 'Commencer le test'}
          </button>
        </form>
      )}

      {sessionId && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/80">
          <p>Assessment ID: {assessmentId}</p>
          <p>Session ID: {sessionId}</p>
          <p>
            Progression: {Math.min(questionIndex, totalQuestions)}/{totalQuestions} ({progressPct}%)
          </p>
        </div>
      )}

      {isRunning && question && (
        <form onSubmit={handleSubmitAnswer} className="space-y-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-3">
            <p className="text-xs uppercase tracking-[0.2em] text-white/50">
              Question {questionIndex} / {totalQuestions}
            </p>
            <p className="text-base text-white font-medium">{question.question_text}</p>
            <div className="space-y-2">
              {question.options.map((option) => (
                <label key={option} className="flex items-start gap-2 rounded-xl border border-white/10 bg-white/3 px-3 py-2">
                  <input
                    type="radio"
                    name="answer"
                    value={option}
                    checked={selectedAnswer === option}
                    onChange={(e) => setSelectedAnswer(e.target.value)}
                  />
                  <span>{option}</span>
                </label>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !selectedAnswer}
            className="inline-flex justify-center rounded-full bg-white text-midnight px-6 py-2 text-sm font-semibold hover:bg-mist transition disabled:opacity-60"
          >
            {loading ? 'Envoi...' : 'Valider la réponse'}
          </button>
        </form>
      )}

      {isCompleted && (
        <div className="rounded-2xl border border-emerald-300/30 bg-emerald-500/10 p-4 text-sm text-emerald-100 space-y-2">
          <p className="font-semibold">Test terminé</p>
          <p>
            Score: {Math.round(lastResult?.results?.percentage ?? 0)}% ({lastResult?.results?.correct_answers ?? 0}/
            {lastResult?.results?.total_questions ?? totalQuestions})
          </p>
          <button
            type="button"
            onClick={resetRunner}
            className="inline-flex rounded-full bg-white text-midnight px-5 py-2 text-xs font-semibold hover:bg-mist transition"
          >
            Refaire un test
          </button>
        </div>
      )}

      {lastResult && !lastResult.quiz_completed && (
        <p className="text-xs text-white/60">
          Dernière réponse: {lastResult.is_correct ? 'correcte' : 'incorrecte'}
        </p>
      )}

      {error && <p className="text-sm text-rose-300">{error}</p>}
    </section>
  );
}
