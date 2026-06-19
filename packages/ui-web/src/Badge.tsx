import type { BadgeProps, BadgeTone } from '@smartinv/ui-contracts';

const TONE_CLASSES: Record<BadgeTone, string> = {
  ok: 'bg-ok-soft text-ok',
  warn: 'bg-warn-soft text-warn-dark',
  crit: 'bg-crit-soft text-crit',
};

const BASE =
  'inline-flex items-center gap-1.5 rounded-pill px-2 py-0.5 text-xs font-medium whitespace-nowrap';
// The reference badge carries a leading status dot (.badge::before); the AI
// chip is dot-less (.b-ai.nodot).
const DOT = "before:content-[''] before:w-1.5 before:h-1.5 before:rounded-pill before:bg-current";

/** Status / AI / neutral label chip. `ai` is violet, reserved for AI content. */
export function Badge({ label, variant = 'neutral', tone = 'ok' }: BadgeProps) {
  const variantClass =
    variant === 'ai'
      ? 'bg-ai-soft text-ai'
      : variant === 'status'
        ? `${TONE_CLASSES[tone]} ${DOT}`
        : `bg-surface text-ink-2 ${DOT}`;
  return <span className={`${BASE} ${variantClass}`}>{label}</span>;
}
