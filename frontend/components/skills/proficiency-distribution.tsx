interface ProficiencyDistributionProps {
  data: Array<{ level: string; count: number }>;
}

const levelLabels: Record<string, string> = {
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  advanced: 'Advanced',
  expert: 'Expert',
};

export function ProficiencyDistribution({ data }: ProficiencyDistributionProps) {
  const total = data.reduce((sum, item) => sum + item.count, 0) || 1;

  return (
    <section className="glass-panel p-6 flex flex-col gap-5">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Skill maturity</p>
        <p className="text-2xl font-semibold mt-1">Proficiency distribution</p>
      </div>
      <div className="space-y-4">
        {data.map((item) => {
          const percentage = Math.round((item.count / total) * 100);
          return (
            <div key={item.level}>
              <div className="flex items-center justify-between text-sm text-white/70">
                <span className="capitalize">{levelLabels[item.level] ?? item.level}</span>
                <span>{percentage}%</span>
              </div>
              <div className="mt-2 h-2 rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-aurora to-corail"
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
