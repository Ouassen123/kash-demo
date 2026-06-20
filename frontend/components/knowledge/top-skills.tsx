interface TopSkillsProps {
  skills: string[];
}

export function TopSkillsList({ skills }: TopSkillsProps) {
  return (
    <section className="glass-panel p-6 flex flex-col gap-4">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Top competencies</p>
        <p className="text-2xl font-semibold mt-1">Skills extracted from CV</p>
      </div>
      <div className="flex flex-wrap gap-2 text-sm text-white/80">
        {skills.length ? (
          skills.map((skill) => (
            <span key={skill} className="rounded-full border border-white/15 px-3 py-1">
              {skill}
            </span>
          ))
        ) : (
          <span className="text-white/60">No skills detected yet.</span>
        )}
      </div>
    </section>
  );
}
