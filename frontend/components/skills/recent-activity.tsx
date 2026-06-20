interface RecentActivityProps {
  items: Array<{
    assessment_id: string;
    project_name: string;
    source_type: string;
    score: number;
    languages: string[];
    completed_at?: string | null;
  }>;
}

function formatDate(value?: string | null) {
  if (!value) return 'Pending';
  try {
    return new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch (error) {
    return value;
  }
}

export function RecentActivityList({ items }: RecentActivityProps) {
  if (!items.length) {
    return (
      <section className="glass-panel p-6">
        <p className="text-sm text-white/70">No recent activity recorded yet.</p>
      </section>
    );
  }

  return (
    <section className="glass-panel p-6 space-y-5">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Latest runs</p>
        <p className="text-2xl font-semibold mt-1">Recent assessments</p>
      </div>
      <div className="space-y-3">
        {items.map((activity) => (
          <article key={activity.assessment_id} className="rounded-3xl border border-white/10 bg-white/3 p-4">
            <div className="flex items-center justify-between text-sm text-white/80">
              <p className="font-semibold text-white">{activity.project_name}</p>
              <span>{formatDate(activity.completed_at)}</span>
            </div>
            <div className="mt-2 flex items-center justify-between text-xs uppercase tracking-[0.2em] text-white/50">
              <span>{activity.source_type}</span>
              <span>{Math.round(activity.score)} pts</span>
            </div>
            {activity.languages.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-white/70">
                {activity.languages.map((language) => (
                  <span key={language} className="rounded-full border border-white/15 px-2 py-0.5">
                    {language}
                  </span>
                ))}
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
