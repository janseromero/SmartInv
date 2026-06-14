import type { BadgeProps, BadgeTone } from '@smartinv/ui-contracts';

const TONE_CLASSES: Record<BadgeTone, string> = {
  ok: 'bg-ok-soft text-ok',
  warn: 'bg-warn-soft text-warn',
  crit: 'bg-crit-soft text-crit',
};

const BASE = 'inline-flex items-center rounded-pill px-2 py-0.5 text-xs font-medium';

/** Status / AI / neutral label chip. `ai` is violet, reserved for AI content. */
export function Badge({ label, variant = 'neutral', tone = 'ok' }: BadgeProps) {
  const variantClass =
    variant === 'ai'
      ? 'bg-ai-soft text-ai'
      : variant === 'status'
        ? TONE_CLASSES[tone]
        : 'bg-surface text-ink-2';
  return <span className={`${BASE} ${variantClass}`}>{label}</span>;
}
