interface AbilitiesRecommendationsProps {
  recommendations: string[];
}

export function AbilitiesRecommendations({ recommendations }: AbilitiesRecommendationsProps) {
  return (
    <section className="glass-panel p-6 flex flex-col gap-4">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Coaching cues</p>
        <p className="text-2xl font-semibold mt-1">Recommended focus</p>
      </div>
      <div className="space-y-3">
        {recommendations.length ? (
          recommendations.map((rec, idx) => (
            <article key={`${rec}-${idx}`} className="rounded-3xl border border-white/10 bg-white/3 p-4 text-sm text-white/80">
              {rec}
            </article>
          ))
        ) : (
          <p className="text-sm text-white/60">No recommendations yet. Complete an abilities quiz to generate insights.</p>
        )}
      </div>
    </section>
  );
}
