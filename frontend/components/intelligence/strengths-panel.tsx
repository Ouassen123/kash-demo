export function IntelligenceStrengthsPanel({
  strengths,
  improvementAreas,
}: {
  strengths: string[];
  improvementAreas: string[];
}) {
  return (
    <section className="glass-panel p-6 grid gap-6 md:grid-cols-2">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Strengths</p>
        <div className="mt-3 space-y-2 text-sm text-white/80">
          {strengths.length ? (
            strengths.map((item) => (
              <div key={item} className="flex items-start gap-2">
                <span className="mt-1 inline-flex h-2 w-2 rounded-full bg-emerald-300" />
                <span>{item}</span>
              </div>
            ))
          ) : (
            <p className="text-white/60">No strengths identified yet.</p>
          )}
        </div>
      </div>
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Improvement areas</p>
        <div className="mt-3 space-y-2 text-sm text-white/80">
          {improvementAreas.length ? (
            improvementAreas.map((item) => (
              <div key={item} className="flex items-start gap-2">
                <span className="mt-1 inline-flex h-2 w-2 rounded-full bg-rose-300" />
                <span>{item}</span>
              </div>
            ))
          ) : (
            <p className="text-white/60">No improvement areas logged.</p>
          )}
        </div>
      </div>
    </section>
  );
}
