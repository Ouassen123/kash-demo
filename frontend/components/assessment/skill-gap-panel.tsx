import { IntelligenceAssessmentDetail } from '@/lib/types';

interface SkillGapPanelProps {
  analysis: IntelligenceAssessmentDetail['skill_gap_analysis'];
}

export function SkillGapPanel({ analysis }: SkillGapPanelProps) {
  if (!analysis?.length) {
    return (
      <section className="glass-panel p-6">
        <p className="text-sm text-white/70">Skill gap analysis not available for this assessment.</p>
      </section>
    );
  }

  const primary = analysis[0];
  const timeline = (primary.development_timeline ?? {}) as Record<string, string>;
  const priorityGaps = (primary.priority_gaps ?? primary.skill_gaps ?? []) as string[];
  const requiredSkills = (primary.required_skills ?? {}) as Record<string, number>;
  const currentSkills = (primary.current_skills ?? {}) as Record<string, number>;

  return (
    <section className="glass-panel p-6 flex flex-col gap-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Skill gap focus</p>
        <p className="text-2xl font-semibold mt-1 capitalize">{primary.target_role?.replace('_', ' ')}</p>
        <p className="text-sm text-white/60">Experience level: {primary.experience_level ?? 'n/a'}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Priority gaps</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {priorityGaps.map((gap: string) => (
              <span key={gap} className="rounded-full border border-white/15 px-3 py-1 text-xs text-rose-200/90">
                {gap}
              </span>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Development timeline</p>
          <div className="mt-2 flex flex-wrap gap-2 text-xs text-white/70">
            {Object.entries(timeline).map(([skill, eta]) => (
              <span key={skill} className="rounded-full border border-white/15 px-3 py-1">
                {skill}: {eta}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Current proficiency</p>
          <div className="mt-3 space-y-2">
            {Object.entries(currentSkills).map(([skill, score]) => (
              <div key={skill} className="text-sm text-white/70">
                <div className="flex items-center justify-between">
                  <span>{skill}</span>
                  <span>{Math.round(Number(score) * 100)}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/10">
                  <div className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-200" style={{ width: `${Math.min(Number(score) * 100, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">Required proficiency</p>
          <div className="mt-3 space-y-2">
            {Object.entries(requiredSkills).map(([skill, score]) => (
              <div key={skill} className="text-sm text-white/70">
                <div className="flex items-center justify-between">
                  <span>{skill}</span>
                  <span>{Math.round(Number(score) * 100)}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/10">
                  <div className="h-full rounded-full bg-gradient-to-r from-amber-400 to-rose-300" style={{ width: `${Math.min(Number(score) * 100, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
