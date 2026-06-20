'use client';

import { FeatureImportanceItem } from '@/lib/types';
import { useMemo } from 'react';

interface FeatureImportanceProps {
  items: FeatureImportanceItem[];
}

const directionColors: Record<FeatureImportanceItem['direction'], string> = {
  positive: 'text-emerald-300',
  negative: 'text-rose-300',
  neutral: 'text-mist/80',
};

export function FeatureImportanceChart({ items }: FeatureImportanceProps) {
  const data = useMemo(() => {
    return items
      .slice()
      .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
      .slice(0, 6);
  }, [items]);

  if (!data.length) {
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
        <p className="text-2xl font-semibold mt-1">Top feature contributions</p>
      </div>
      <div className="space-y-4">
        {data.map((item) => (
          <article key={item.feature_name} className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-sm text-white/70">
              <div>
                <p className="font-medium text-white/90">{item.feature_name}</p>
                <p className="text-xs text-white/50">{item.explanation}</p>
              </div>
              <span className={`text-sm font-semibold ${directionColors[item.direction]}`}>
                {item.direction === 'positive' ? '+' : item.direction === 'negative' ? '-' : ''}
                {Math.abs(item.shap_value).toFixed(2)}
              </span>
            </div>
            <div className="h-2 rounded-full bg-white/10">
              <div
                className={`h-full rounded-full ${item.direction === 'negative' ? 'bg-gradient-to-r from-rose-500 to-rose-300' : 'bg-gradient-to-r from-emerald-400 to-emerald-200'}`}
                style={{ width: `${Math.min(Math.abs(item.contribution_percentage), 100)}%` }}
              />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
