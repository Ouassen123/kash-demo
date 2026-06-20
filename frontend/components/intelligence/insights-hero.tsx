import { stageTaglines } from '@/lib/dashboard';

interface InsightsHeroProps {
  data: {
    overallScore: number;
    confidence: number;
    careerStage: string;
    totalAssessments: number;
    lastUpdated: string;
  };
}

function formatDate(value?: string) {
  if (!value) return 'Not available';
  try {
    return new Date(value).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    return value;
  }
}

export function InsightsHero({ data }: InsightsHeroProps) {
  const tagline = stageTaglines[data.careerStage] ?? stageTaglines.explorer;

  return (
    <section className="glass-panel p-6 grid gap-6 md:grid-cols-[2fr,1fr]">
      <div className="flex flex-col gap-6">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Intelligence overview</p>
          <h1 className="text-3xl font-semibold mt-2 text-white">Holistic KASH insights</h1>
          <p className="text-sm text-white/70 mt-3 max-w-2xl">{tagline}</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Overall score</p>
            <p className="text-4xl font-semibold mt-2">{Math.round(data.overallScore)}</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Confidence</p>
            <p className="text-4xl font-semibold mt-2">{Math.round(data.confidence * 100)}%</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Assessments</p>
            <p className="text-4xl font-semibold mt-2">{data.totalAssessments}</p>
          </div>
        </div>
      </div>
      <div className="rounded-3xl border border-white/10 bg-white/5 p-5 flex flex-col gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Career stage</p>
          <p className="text-2xl font-semibold mt-1 capitalize">{data.careerStage}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Last updated</p>
          <p className="text-sm text-white/80 mt-1">{formatDate(data.lastUpdated)}</p>
        </div>
      </div>
    </section>
  );
}
