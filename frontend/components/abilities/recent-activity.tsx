import { AbilitiesRecentActivityItem } from '@/lib/types';

export function AbilitiesRecentActivity({ items }: { items: AbilitiesRecentActivityItem[] }) {
  if (!items.length) {
    return (
      <section className="glass-panel p-6">
        <p className="text-sm text-white/70">No recent abilities assessments yet.</p>
      </section>
    );
  }

  return (
    <section className="glass-panel p-6 space-y-4">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Recent sessions</p>
        <p className="text-2xl font-semibold mt-1">Assessment activity</p>
      </div>
      <div className="space-y-3">
        {items.map((activity) => (
          <article key={activity.assessment_id} className="rounded-3xl border border-white/10 bg-white/3 p-4">
            <div className="flex items-center justify-between text-sm text-white/80">
              <p className="font-semibold text-white capitalize">{activity.domain?.replace('_', ' ')}</p>
              <span>{Math.round(activity.score)}%</span>
            </div>
            <p className="text-xs text-white/60 mt-1">
              Completed {activity.completed_at ? new Date(activity.completed_at).toLocaleDateString() : '—'}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
