interface SkillsRecommendationsProps {
  items: string[];
}

export function SkillsRecommendations({ items }: SkillsRecommendationsProps) {
  return (
    <section className="glass-panel p-6 flex flex-col gap-4">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Guided next steps</p>
        <p className="text-2xl font-semibold mt-1">Recommendations</p>
      </div>
      <div className="space-y-3">
        {items.map((item, idx) => (
          <article key={`${item}-${idx}`} className="rounded-3xl border border-white/10 bg-white/3 p-4 text-sm text-white/80">
            <p>{item}</p>
          </article>
        ))}
        {!items.length && <p className="text-sm text-white/60">No recommendations available.</p>}
      </div>
    </section>
  );
}
