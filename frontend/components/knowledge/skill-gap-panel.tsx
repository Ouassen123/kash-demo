import { KnowledgeSkillGap } from '@/lib/types';

interface KnowledgeSkillGapPanelProps {
  gaps: KnowledgeSkillGap[];
}

const priorityTokens: Record<KnowledgeSkillGap['priority'], { label: string; className: string }> = {
  high: { label: 'High priority', className: 'text-rose-200 bg-rose-500/10 border-rose-400/30' },
  medium: { label: 'Medium', className: 'text-amber-200 bg-amber-500/10 border-amber-400/30' },
  low: { label: 'Monitor', className: 'text-mist/80 bg-white/5 border-white/20' },
};

export function KnowledgeSkillGapPanel({ gaps }: KnowledgeSkillGapPanelProps) {
  if (!gaps.length) {
    return (
      <section className="glass-panel p-6">
        <p className="text-sm text-white/70">No skill gaps detected yet.</p>
      </section>
    );
  }

  return (
    <section className="glass-panel p-6 space-y-4">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Gap analysis</p>
        <p className="text-2xl font-semibold mt-1">Occupation readiness</p>
      </div>
      <div className="space-y-4">
        {gaps.map((gap) => {
          const token = priorityTokens[gap.priority];
          return (
            <article key={gap.occupation} className="rounded-3xl border border-white/10 bg-white/3 p-4 flex flex-col gap-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-white/90 font-semibold capitalize">{gap.occupation.replace('_', ' ')}</p>
                  <p className="text-xs text-white/60">Coverage: {Math.round(gap.skill_coverage * 100)}%</p>
                </div>
                <span className={`px-3 py-1 text-xs rounded-full border ${token.className}`}>{token.label}</span>
              </div>
              <div className="flex flex-wrap gap-2 text-xs text-white/80">
                {gap.missing_skills.map((skill) => (
                  <span key={skill} className="rounded-full border border-white/15 px-3 py-1">
                    {skill}
                  </span>
                ))}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
