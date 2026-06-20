import { DomainScore } from '@/lib/types';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

const domainColors: Record<DomainScore['key'], string> = {
  knowledge: 'from-[#4AE3B5] to-[#178F66]',
  abilities: 'from-[#8E7CFF] to-[#4C3BCE]',
  skills: 'from-[#FFB347] to-[#FF7C6E]',
  experience: 'from-[#6FB1FC] to-[#365CFF]',
};

export function DomainScoreCard({ domain }: { domain: DomainScore }) {
  const trendIcon = domain.trend > 1 ? <ArrowUpRight className="text-emerald-400" size={16} /> : domain.trend < -1 ? <ArrowDownRight className="text-rose-400" size={16} /> : <Minus className="text-zinc-400" size={16} />;
  const trendLabel = domain.trend > 1 ? 'Improving' : domain.trend < -1 ? 'Declining' : 'Stable';

  return (
    <article className="glass-panel p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.25em] text-mist/70">{domain.label}</p>
          <p className="text-4xl font-semibold mt-1">{Math.round(domain.score)}</p>
        </div>
        <div className={`h-12 w-12 rounded-full bg-gradient-to-br ${domainColors[domain.key]} flex items-center justify-center text-midnight font-semibold`}>
          {Math.round(domain.confidence * 100)}%
        </div>
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
