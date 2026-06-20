import { BadgeCheck } from 'lucide-react';

interface OverallScoreHeroProps {
  overallScore: number;
  confidence: number;
  careerStage: string;
  stageTagline: string;
  lastUpdated: string;
}

const stageTokens: Record<string, { label: string; accent: string }> = {
  explorer: { label: 'Explorer', accent: 'text-emerald-300 bg-emerald-500/10' },
  beginner: { label: 'Beginner', accent: 'text-sky-300 bg-sky-500/10' },
  intermediate: { label: 'Intermediate', accent: 'text-violet-300 bg-violet-500/10' },
  advanced: { label: 'Advanced', accent: 'text-amber-300 bg-amber-500/10' },
  expert: { label: 'Expert', accent: 'text-rose-300 bg-rose-500/10' },
};

function formatDate(input: string) {
  try {
    return new Date(input).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    return 'Not available';
  }
}

export function OverallScoreHero({ overallScore, confidence, careerStage, stageTagline, lastUpdated }: OverallScoreHeroProps) {
  const stage = stageTokens[careerStage] ?? stageTokens.explorer;

  return (
    <section className="glass-panel relative overflow-hidden">
      <div className="absolute inset-0 opacity-70" style={{ background: 'radial-gradient(circle at top, rgba(76,91,255,0.35), transparent 55%)' }} />
      <div className="relative z-10 flex flex-col gap-6 p-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Intelligence Overview</p>
            <div className="flex items-baseline gap-3 mt-1">
              <span className="text-6xl font-semibold tracking-tight">{Math.round(overallScore)}</span>
              <span className="text-white/60">/ 100</span>
            </div>
          </div>
          <div className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm ${stage.accent}`}>
            <BadgeCheck size={16} />
            <span>{stage.label} stage</span>
          </div>
        </div>

        <p className="text-lg text-white/80 max-w-2xl leading-relaxed">{stageTagline}</p>

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-white/10 p-4 bg-white/5">
            <p className="text-xs uppercase tracking-[0.25em] text-white/50">Confidence</p>
            <p className="text-2xl font-semibold mt-2">{Math.round(confidence * 100)}%</p>
            <p className="text-sm text-white/60">Model certainty in latest assessment</p>
          </div>
          <div className="rounded-2xl border border-white/10 p-4 bg-white/5">
            <p className="text-xs uppercase tracking-[0.25em] text-white/50">Stage focus</p>
            <p className="text-2xl font-semibold mt-2 capitalize">{stage.label}</p>
            <p className="text-sm text-white/60">Aligned to KASH trajectory</p>
          </div>
          <div className="rounded-2xl border border-white/10 p-4 bg-white/5">
            <p className="text-xs uppercase tracking-[0.25em] text-white/50">Last synced</p>
            <p className="text-lg font-medium mt-2">{formatDate(lastUpdated)}</p>
            <p className="text-sm text-white/60">Pulls the freshest insights</p>
          </div>
        </div>
      </div>
    </section>
  );
}
