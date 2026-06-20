interface CareerSuggestionsProps {
  suggestions: string[];
}

export function CareerSuggestionsPanel({ suggestions }: CareerSuggestionsProps) {
  return (
    <section className="glass-panel p-6 flex flex-col gap-4">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Career targeting</p>
        <p className="text-2xl font-semibold mt-1">Top matched roles</p>
      </div>
      <div className="space-y-3">
        {suggestions.length ? (
          suggestions.map((career) => (
            <article key={career} className="rounded-3xl border border-white/10 bg-white/3 p-4 text-sm text-white/80">
              {career}
            </article>
          ))
        ) : (
          <p className="text-sm text-white/60">No career suggestions yet. Run a CV analysis to unlock recommendations.</p>
        )}
      </div>
    </section>
  );
}
