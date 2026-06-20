interface LanguageHighlight {
  name: string;
  percentage: number;
}

interface SkillHighlight {
  name: string;
  confidence: number;
}

interface SkillsHighlightsProps {
  languages: LanguageHighlight[];
  topSkills: SkillHighlight[];
}

function ConfidenceBar({ value }: { value: number }) {
  return (
    <div className="h-2 rounded-full bg-white/10">
      <div
        className="h-full rounded-full bg-gradient-to-r from-aurora to-corail"
        style={{ width: `${Math.min(value * 100, 100)}%` }}
      />
    </div>
  );
}

export function SkillsHighlightsPanel({ languages, topSkills }: SkillsHighlightsProps) {
  return (
    <section className="glass-panel p-6 grid gap-8 lg:grid-cols-2">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Language mix</p>
        <p className="text-2xl font-semibold mt-1">Code distribution</p>
        <div className="mt-6 space-y-4">
          {languages.map((language) => (
            <div key={language.name} className="flex items-center gap-3">
              <div className="w-24 text-sm text-white/70">{language.name}</div>
              <div className="flex-1 h-2 rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-[#6FB1FC] to-[#365CFF]"
                  style={{ width: `${language.percentage}%` }}
                />
              </div>
              <span className="w-10 text-right text-sm text-white/70">{language.percentage}%</span>
            </div>
          ))}
        </div>
      </div>
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Top strengths</p>
        <p className="text-2xl font-semibold mt-1">Skill confidence</p>
        <div className="mt-6 space-y-5">
          {topSkills.map((skill) => (
            <div key={skill.name}>
              <div className="flex items-center justify-between text-sm text-white/70">
                <span>{skill.name}</span>
                <span>{Math.round(skill.confidence * 100)}%</span>
              </div>
              <ConfidenceBar value={skill.confidence} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
