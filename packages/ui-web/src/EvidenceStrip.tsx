import type { EvidenceItem, EvidenceStripProps } from '@smartinv/ui-contracts';
import { ConfidenceMeter } from './ConfidenceMeter.js';

function Chip({ item }: { item: EvidenceItem }) {
  const chip = (
    <span className="inline-flex items-center gap-1 rounded-md bg-surface border border-line px-2 py-1 text-xs">
      <span className="text-ink-3">{item.metric}</span>
      <span className="font-mono text-ink">{item.value}</span>
    </span>
  );
  return item.sourceHref ? (
    <a href={item.sourceHref} className="no-underline">
      {chip}
    </a>
  ) : (
    chip
  );
}

/** Evidence chips + confidence + model version — the recommendation envelope UI. */
export function EvidenceStrip({
  items,
  confidence,
  modelVersion,
  loading = false,
}: EvidenceStripProps) {
  if (loading) {
    return (
      <div className="bg-card border border-line rounded-lg p-md animate-pulse">
        <div className="h-4 w-40 bg-line rounded" />
      </div>
    );
  }

  return (
    <div className="bg-card border border-line rounded-lg p-md flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <Chip key={`${item.metric}-${item.value}`} item={item} />
        ))}
      </div>
      {confidence !== undefined ? <ConfidenceMeter value={confidence} /> : null}
      {modelVersion ? (
        <span className="font-mono text-[10px] text-ink-3">model {modelVersion}</span>
      ) : null}
    </div>
  );
}
