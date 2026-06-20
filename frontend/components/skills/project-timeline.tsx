interface ProjectTimelineProps {
  items: Array<{ date: string; complexity: number; project_name: string }>;
}

function formatDate(value: string) {
  try {
    return new Date(value).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    });
  } catch (error) {
    return value;
  }
}

export function ProjectTimeline({ items }: ProjectTimelineProps) {
  if (!items.length) {
    return (
      <section className="glass-panel p-6">
        <p className="text-sm text-white/70">No project timeline data available.</p>
      </section>
    );
  }

  return (
    <section className="glass-panel p-6 space-y-5">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Project complexity</p>
        <p className="text-2xl font-semibold mt-1">Recent work timeline</p>
      </div>
      <div className="space-y-4">
        {items.map((item, index) => (
          <article key={`${item.project_name}-${index}`} className="flex items-center gap-4">
            <div className="text-sm text-white/60 w-16">{formatDate(item.date)}</div>
            <div className="flex-1">
              <div className="flex items-center justify-between text-sm text-white/70">
                <p className="font-semibold text-white/90">{item.project_name}</p>
                <span>{Math.round(item.complexity)} complexity</span>
              </div>
              <div className="mt-2 h-1.5 rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-aurora to-corail"
                  style={{ width: `${Math.min(item.complexity, 100)}%` }}
                />
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
