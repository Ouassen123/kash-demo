import { AssessmentActivity } from '@/lib/types';
import { Clock3, Activity } from 'lucide-react';

const statusTokens: Record<AssessmentActivity['status'], { label: string; color: string }> = {
  completed: { label: 'Completed', color: 'text-emerald-300 bg-emerald-500/10' },
  in_progress: { label: 'Running', color: 'text-amber-300 bg-amber-500/10' },
  queued: { label: 'Queued', color: 'text-mist/60 bg-white/5' },
};

function formatDate(date: string) {
  try {
    return new Date(date).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    return date;
  }
}

export function AssessmentActivityTimeline({ items }: { items: AssessmentActivity[] }) {
  return (
    <section className="glass-panel p-6 flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <Activity size={18} className="text-aurora" />
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Assessments</p>
          <p className="text-2xl font-semibold mt-1">Recent activity</p>
        </div>
      </div>
      <div className="flex flex-col gap-4">
        {items.map((item) => {
          const token = statusTokens[item.status];
          return (
            <article key={item.id} className="flex items-start gap-4">
              <div className="h-full w-px bg-gradient-to-b from-white/40 via-white/10 to-transparent" />
              <div className="flex-1 border border-white/10 rounded-3xl p-4 bg-white/3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm text-white/60">{formatDate(item.date)}</p>
                    <h4 className="text-lg font-semibold text-white/90 mt-1">{item.title}</h4>
                  </div>
                  <span className={`px-3 py-1 text-xs rounded-full ${token.color}`}>{token.label}</span>
                </div>
                <div className="mt-3 flex items-center justify-between text-sm text-white/70">
                  <div className="flex items-center gap-2">
                    <Clock3 size={14} />
                    <span>{item.module.toUpperCase()}</span>
                  </div>
                  <span className="text-white font-semibold">{Math.round(item.score)} pts</span>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
