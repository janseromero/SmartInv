import type { ButtonProps, ButtonSize, ButtonVariant } from '@smartinv/ui-contracts';
import type { ButtonHTMLAttributes } from 'react';

const VARIANT: Record<ButtonVariant, string> = {
  // The reference `.btn` system: teal is the primary action color; violet (ai)
  // is reserved for AI-triggered actions (non-negotiable #8).
  default: 'bg-card border border-line text-ink hover:border-ink-3 shadow-card',
  primary: 'bg-teal border border-teal text-white hover:bg-teal-dark',
  ai: 'bg-ai border border-ai text-white',
  ghost: 'bg-transparent border border-transparent text-ink-2 hover:bg-surface',
};

const SIZE: Record<ButtonSize, string> = {
  md: 'px-md py-1.5 text-sm rounded-md',
  sm: 'px-2.5 py-1 text-xs rounded-sm',
};

const BASE =
  'inline-flex items-center justify-center gap-2 font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed';

/** Token-styled button matching the reference `.btn` system. */
export function Button({
  variant = 'default',
  size = 'md',
  type = 'button',
  className = '',
  ...props
}: ButtonProps & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type={type}
      className={`${BASE} ${VARIANT[variant]} ${SIZE[size]} ${className}`}
      {...props}
    />
  );
}
