interface SkillCategoryChartProps {
  categories: Array<{ category: string; count: number }>;
}

export function SkillCategoryChart({ categories }: SkillCategoryChartProps) {
  const total = categories.reduce((sum, item) => sum + item.count, 0) || 1;

  return (
    <section className="glass-panel p-6 flex flex-col gap-5">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Skill taxonomy</p>
        <p className="text-2xl font-semibold mt-1">Categories detected</p>
      </div>
      <div className="space-y-4">
        {categories.map((item) => {
          const percentage = Math.round((item.count / total) * 100);
          return (
            <div key={item.category}>
              <div className="flex items-center justify-between text-sm text-white/70">
                <span className="capitalize">{item.category.replace('_', ' ')}</span>
                <span>{percentage}%</span>
              </div>
              <div className="mt-2 h-2 rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-[#4AE3B5] to-[#178F66]"
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
