import type { KpiCardProps, KpiStatus, KpiTrend } from '@smartinv/ui-contracts';

const STATUS_DOT: Record<KpiStatus, string> = {
  ok: 'bg-ok',
  warn: 'bg-warn',
  crit: 'bg-crit',
};

const TREND_TEXT: Record<KpiTrend, string> = {
  up: 'text-ok',
  down: 'text-crit',
  flat: 'text-ink-3',
};

const TREND_GLYPH: Record<KpiTrend, string> = {
  up: '▲',
  down: '▼',
  flat: '→',
};

/** A single key-performance-indicator tile. */
export function KpiCard({
  label,
  value,
  unit,
  delta,
  trend,
  status,
  loading = false,
  dense = false,
}: KpiCardProps) {
  const pad = dense ? 'p-md' : 'p-lg';

  if (loading) {
    return (
      <div className={`bg-card border border-line rounded-lg ${pad} animate-pulse`}>
        <div className="h-3 w-20 bg-line rounded" />
        <div className="mt-3 h-6 w-28 bg-line rounded" />
      </div>
    );
  }

  return (
    <div className={`bg-card border border-line rounded-lg ${pad}`}>
      <div className="flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-wide text-ink-3">{label}</span>
        {status ? <span className={`w-2 h-2 rounded-pill ${STATUS_DOT[status]}`} /> : null}
      </div>
      <div className="mt-2 flex items-baseline gap-1">
        <span className="font-display text-2xl text-ink">{value}</span>
        {unit ? <span className="text-sm text-ink-3">{unit}</span> : null}
      </div>
      {delta ? (
        <div className={`mt-1 text-xs ${trend ? TREND_TEXT[trend] : 'text-ink-3'}`}>
          {trend ? `${TREND_GLYPH[trend]} ` : ''}
          {delta}
        </div>
      ) : null}
    </div>
  );
}
