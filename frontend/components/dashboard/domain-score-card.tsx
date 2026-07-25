import { DomainScore } from '@/lib/types';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

const domainColors: Record<DomainScore['key'], { gradient: string; bar: string; text: string }> = {
  knowledge: { gradient: 'from-[#4AE3B5] to-[#178F66]', bar: 'bg-gradient-to-r from-[#4AE3B5] to-[#178F66]', text: 'text-knowledge' },
  abilities: { gradient: 'from-[#8E7CFF] to-[#4C3BCE]', bar: 'bg-gradient-to-r from-[#8E7CFF] to-[#4C3BCE]', text: 'text-abilities' },
  skills: { gradient: 'from-[#FFB347] to-[#FF7C6E]', bar: 'bg-gradient-to-r from-[#FFB347] to-[#FF7C6E]', text: 'text-skills' },
  experience: { gradient: 'from-[#6FB1FC] to-[#365CFF]', bar: 'bg-gradient-to-r from-[#6FB1FC] to-[#365CFF]', text: 'text-habits' },
};

export function DomainScoreCard({ domain }: { domain: DomainScore }) {
  const trendIcon = domain.trend > 1 ? <ArrowUpRight className="text-emerald-400" size={16} /> : domain.trend < -1 ? <ArrowDownRight className="text-rose-400" size={16} /> : <Minus className="text-zinc-400" size={16} />;
  const trendLabel = domain.trend > 1 ? 'Improving' : domain.trend < -1 ? 'Declining' : 'Stable';

  const colors = domainColors[domain.key];

  return (
    <article className="glass-card p-5 flex flex-col gap-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.25em] text-mist/70">{domain.label}</p>
          <p className={`text-4xl font-bold mt-1 ${colors.text}`}>{Math.round(domain.score)}</p>
        </div>
        <div className={`h-12 w-12 rounded-full bg-gradient-to-br ${colors.gradient} flex items-center justify-center text-midnight font-semibold shadow-lg`}>
          {Math.round(domain.confidence * 100)}%
        </div>
      </div>
      <div className="progress-bar">
        <div className={`progress-fill ${colors.bar}`} style={{ width: `${Math.min(domain.score, 100)}%` }} />
      </div>
      <div className="flex items-center justify-between border-t border-white/10 pt-3">
        <div className="flex items-center gap-2 text-sm text-white/70">
          {trendIcon}
          <span>{trendLabel}</span>
        </div>
        <span className="text-xs text-white/50">Δ {domain.trend > 0 ? '+' : ''}{domain.trend.toFixed(1)} pts</span>
      </div>
    </article>
  );
}
