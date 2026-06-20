interface CategoryGridProps {
  categories: Array<{
    name: string;
    skills: Array<{ name: string; confidence: number; proficiency_level: string }>;
  }>;
}

const proficiencyColors: Record<string, string> = {
  beginner: 'text-rose-200/90',
  intermediate: 'text-amber-200/90',
  advanced: 'text-emerald-200/90',
  expert: 'text-sky-200/90',
};

export function CategoryGrid({ categories }: CategoryGridProps) {
  return (
    <section className="glass-panel p-6 space-y-5">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Skill clusters</p>
        <p className="text-2xl font-semibold mt-1">Top proficiencies</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {categories.map((category) => (
          <article key={category.name} className="rounded-3xl border border-white/10 bg-white/3 p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-white/90 font-semibold capitalize">{category.name.replace('_', ' ')}</p>
              <span className="text-xs text-white/50">{category.skills.length} skills</span>
            </div>
            <div className="space-y-3">
              {category.skills.map((skill) => (
                <div key={skill.name} className="text-sm text-white/70">
                  <div className="flex items-center justify-between">
                    <span>{skill.name}</span>
                    <span className={`text-xs uppercase tracking-[0.2em] ${proficiencyColors[skill.proficiency_level] ?? 'text-white/60'}`}>
                      {skill.proficiency_level}
                    </span>
                  </div>
                  <div className="mt-1 h-1.5 rounded-full bg-white/10">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-aurora to-corail"
                      style={{ width: `${Math.min(skill.confidence * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
