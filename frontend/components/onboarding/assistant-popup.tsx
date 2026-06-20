'use client';

import { useState, useEffect } from 'react';
import { X, ChevronRight, ChevronLeft, Brain, FileText, Video, Code, Trophy } from 'lucide-react';

const STEPS = [
  {
    icon: <Trophy size={28} className="text-amber-300" />,
    title: 'Bienvenue sur KASH !',
    description: 'KASH mesure ton profil professionnel en 4 dimensions : Knowledge, Abilities, Skills, et Holistic Intelligence.',
    tip: 'Le résultat final donne un score sur 100 avec des recommandations personnalisées.',
    color: 'border-amber-400/30 bg-amber-500/5',
  },
  {
    icon: <Brain size={28} className="text-violet-300" />,
    title: '1) Abilities — Quiz cognitif',
    description: 'Un quiz adaptatif de 5 questions qui mesure ta mémoire, logique, attention et raisonnement spatial.',
    tip: '💡 Réponds sérieusement — le système adapte la difficulté selon tes réponses (algorithme IRT).',
    color: 'border-violet-400/30 bg-violet-500/5',
  },
  {
    icon: <FileText size={28} className="text-emerald-300" />,
    title: '2) Knowledge — Upload CV',
    description: 'Upload ton CV en PDF, DOCX ou TXT. Le système analyse tes compétences via TF-IDF et KNN.',
    tip: '💡 Plus ton CV est détaillé (compétences, expériences, formations), meilleur sera ton score.',
    color: 'border-emerald-400/30 bg-emerald-500/5',
  },
  {
    icon: <Video size={28} className="text-blue-300" />,
    title: '3) Entretien webcam',
    description: 'Réponds à 3 questions sur tes objectifs, tes défis et tes axes d\'amélioration.',
    tip: '💡 Chaque réponse doit faire au moins 10 mots. Sois précis et concret.',
    color: 'border-blue-400/30 bg-blue-500/5',
  },
  {
    icon: <Code size={28} className="text-rose-300" />,
    title: '4) Skills — Upload code',
    description: 'Upload un fichier de code (.py, .js, .ts, etc.) pour analyser tes compétences techniques.',
    tip: '💡 Un fichier avec des imports, fonctions et classes donnera un meilleur score.',
    color: 'border-rose-400/30 bg-rose-500/5',
  },
];

const STORAGE_KEY = 'kash_onboarding_done';

export function AssistantPopup() {
  const [visible, setVisible] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    const done = localStorage.getItem(STORAGE_KEY);
    if (!done) {
      const timer = setTimeout(() => setVisible(true), 800);
      return () => clearTimeout(timer);
    }
  }, []);

  function dismiss() {
    localStorage.setItem(STORAGE_KEY, '1');
    setVisible(false);
  }

  function next() {
    if (step < STEPS.length - 1) setStep(step + 1);
    else dismiss();
  }

  function prev() {
    if (step > 0) setStep(step - 1);
  }

  if (!visible) return (
    <button
      onClick={() => setVisible(true)}
      className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full bg-indigo-500 px-4 py-2.5 text-xs font-semibold text-white shadow-lg hover:bg-indigo-400 transition"
      title="Guide KASH"
    >
      <span className="text-base">💬</span> Guide KASH
    </button>
  );

  const current = STEPS[step];

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm" onClick={dismiss} />

      {/* Popup */}
      <div className={`fixed bottom-6 right-6 z-50 w-80 rounded-2xl border ${current.color} p-5 shadow-2xl backdrop-blur-md transition-all`}>
        {/* Close */}
        <button onClick={dismiss} className="absolute right-4 top-4 text-white/40 hover:text-white transition">
          <X size={16} />
        </button>

        {/* Progress dots */}
        <div className="flex gap-1.5 mb-4">
          {STEPS.map((_, i) => (
            <div
              key={i}
              onClick={() => setStep(i)}
              className={`h-1.5 rounded-full cursor-pointer transition-all ${i === step ? 'bg-white w-6' : 'bg-white/20 w-1.5'}`}
            />
          ))}
        </div>

        {/* Content */}
        <div className="flex gap-3 mb-3">
          <div className="shrink-0 mt-0.5">{current.icon}</div>
          <div>
            <p className="font-semibold text-white text-sm">{current.title}</p>
            <p className="text-xs text-white/70 mt-1 leading-relaxed">{current.description}</p>
          </div>
        </div>

        {/* Tip box */}
        <div className="rounded-xl bg-white/5 border border-white/10 px-3 py-2 text-xs text-white/60 mb-4">
          {current.tip}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={prev}
            disabled={step === 0}
            className="flex items-center gap-1 text-xs text-white/50 hover:text-white disabled:opacity-30 transition"
          >
            <ChevronLeft size={14} /> Précédent
          </button>
          <span className="text-xs text-white/30">{step + 1} / {STEPS.length}</span>
          <button
            onClick={next}
            className="flex items-center gap-1 rounded-full bg-white/15 hover:bg-white/25 px-3 py-1.5 text-xs font-semibold text-white transition"
          >
            {step === STEPS.length - 1 ? 'Commencer !' : 'Suivant'} <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </>
  );
}
