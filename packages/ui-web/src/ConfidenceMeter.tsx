import type { ConfidenceMeterProps } from '@smartinv/ui-contracts';

function fillClass(value: number): string {
  if (value >= 0.75) {
    return 'bg-ok';
  }
  if (value >= 0.4) {
    return 'bg-warn';
  }
  return 'bg-crit';
}

/** Horizontal confidence bar (0..1) with optional threshold bands. */
export function ConfidenceMeter({ value, label, showBands = false }: ConfidenceMeterProps) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-ink-3">{label ?? 'Confidence'}</span>
        <span className="font-mono text-xs text-ink-2">{Math.round(pct)}%</span>
      </div>
      <div className="relative h-2 w-full rounded-pill bg-line overflow-hidden">
        <div className={`h-full rounded-pill ${fillClass(value)}`} style={{ width: `${pct}%` }} />
        {showBands ? (
          <>
            <span className="absolute top-0 h-full w-px bg-surface" style={{ left: '40%' }} />
            <span className="absolute top-0 h-full w-px bg-surface" style={{ left: '75%' }} />
          </>
        ) : null}
      </div>
    </div>
  );
}
