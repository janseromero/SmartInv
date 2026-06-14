import type { ApprovalState, ApprovalStepProps } from '@smartinv/ui-contracts';

interface StateStyle {
  dot: string;
  text: string;
  glyph: string;
}

const STATE_STYLE: Record<ApprovalState, StateStyle> = {
  pending: { dot: 'bg-ink-3', text: 'text-ink-3', glyph: '○' },
  active: { dot: 'bg-teal', text: 'text-ink', glyph: '◔' },
  approved: { dot: 'bg-ok', text: 'text-ink', glyph: '✓' },
  rejected: { dot: 'bg-crit', text: 'text-crit', glyph: '✕' },
};

/** A single step in an approval workflow with its actor. */
export function ApprovalStep({ label, state, actor }: ApprovalStepProps) {
  const style = STATE_STYLE[state];
  return (
    <div className="flex items-center gap-2">
      <span
        className={`grid place-items-center w-5 h-5 rounded-pill text-[10px] text-card ${style.dot}`}
      >
        {style.glyph}
      </span>
      <div className="flex flex-col">
        <span className={`text-sm ${style.text}`}>{label}</span>
        {actor ? <span className="text-xs text-ink-3">{actor}</span> : null}
      </div>
    </div>
  );
}
