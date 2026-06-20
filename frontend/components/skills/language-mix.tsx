interface LanguageMixProps {
  languages: Array<{ name: string; percentage: number; count: number }>;
}

export function LanguageMix({ languages }: LanguageMixProps) {
  return (
    <section className="glass-panel p-6 flex flex-col gap-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Codebase mix</p>
        <p className="text-2xl font-semibold mt-1">Language distribution</p>
      </div>
      <div className="space-y-4">
        {languages.map((language) => (
          <div key={language.name} className="flex items-center gap-3">
            <div className="w-28 text-sm text-white/70">{language.name}</div>
            <div className="flex-1 h-2 rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-gradient-to-r from-[#6FB1FC] to-[#365CFF]"
                style={{ width: `${language.percentage}%` }}
              />
            </div>
            <div className="w-16 text-right text-sm text-white/60">{language.percentage}%</div>
          </div>
        ))}
      </div>
    </section>
  );
}
