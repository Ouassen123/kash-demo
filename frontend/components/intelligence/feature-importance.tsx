import { FeatureImportanceItem } from '@/lib/types';

export function IntelligenceFeatureImportance({ items }: { items: FeatureImportanceItem[] }) {
  if (!items.length) {
    return (
      <section className="glass-panel p-6">
        <p className="text-sm text-white/70">Feature importance data not available.</p>
      </section>
    );
  }

  return (
    <section className="glass-panel p-6 space-y-5">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-mist/70">Explainability</p>
        <p className="text-2xl font-semibold mt-1">Top contributors</p>
      </div>
      <div className="space-y-4">
        {items.map((item) => (
          <article key={item.feature_name} className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-sm text-white/70">
              <div>
                <p className="font-medium text-white/90 capitalize">{item.feature_name}</p>
                <p className="text-xs text-white/50">{item.explanation}</p>
              </div>
              <span
                className={`text-sm font-semibold ${
                  item.direction === 'positive'
                    ? 'text-emerald-300'
                    : item.direction === 'negative'
                    ? 'text-rose-300'
                    : 'text-mist/80'
                }`}
              >
                {item.direction === 'positive' ? '+' : item.direction === 'negative' ? '-' : ''}
                {Math.abs(item.shap_value).toFixed(2)}
              </span>
            </div>
            <div className="h-2 rounded-full bg-white/10">
              <div
                className={`h-full rounded-full ${
                  item.direction === 'negative'
                    ? 'bg-gradient-to-r from-rose-500 to-rose-300'
                    : 'bg-gradient-to-r from-emerald-400 to-emerald-200'
                }`}
                style={{ width: `${Math.min(Math.abs(item.contribution_percentage), 100)}%` }}
              />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
