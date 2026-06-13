/**
 * SmartInv icon set.
 *
 * Inline SVGs lifted from the high-fidelity mock. Kept inline (not a
 * third-party icon library) so CV1.E3 introduces zero new dependencies.
 * When the icon set grows past ~30 glyphs, swap to lucide-react in a
 * follow-up task.
 */
import type { SVGProps } from 'react';

type IconProps = SVGProps<SVGSVGElement>;

const STROKE = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
} satisfies SVGProps<SVGSVGElement>;

export function LogoMarkIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <title>SmartInv</title>
      <path d="M4 17l5-5 4 4 7-8" />
      <path d="M15 8h5v5" />
    </svg>
  );
}

export function GridIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <rect x="3" y="3" width="7" height="9" rx="1.5" />
      <rect x="14" y="3" width="7" height="5" rx="1.5" />
      <rect x="14" y="12" width="7" height="9" rx="1.5" />
      <rect x="3" y="16" width="7" height="5" rx="1.5" />
    </svg>
  );
}

export function ActivityIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <path d="M22 12h-4l-3 8-4-16-3 8H2" />
    </svg>
  );
}

export function TrendIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <path d="M3 17l5-6 4 3 6-8" />
      <circle cx="18" cy="6" r="2" />
    </svg>
  );
}

export function ShuffleIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <circle cx="6" cy="6" r="3" />
      <circle cx="18" cy="18" r="3" />
      <path d="M6 9v3a4 4 0 0 0 4 4h5" />
      <path d="M13 13l3 3-3 3" />
    </svg>
  );
}

export function TriangleAlertIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <path d="M12 3l9 16H3z" />
      <path d="M12 10v4M12 17.5v.1" />
    </svg>
  );
}

export function CartIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <circle cx="9" cy="20" r="1.6" />
      <circle cx="17" cy="20" r="1.6" />
      <path d="M3 4h2l2.5 12h11L21 8H7" />
    </svg>
  );
}

export function ClockIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <path d="M21 12a8 8 0 1 1-4-6.9" />
      <path d="M12 8v4l3 2" />
    </svg>
  );
}

export function AgentBoxIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <rect x="5" y="8" width="14" height="11" rx="2.5" />
      <path d="M12 8V4M8 4h8" />
      <circle cx="9.5" cy="13" r=".8" />
      <circle cx="14.5" cy="13" r=".8" />
    </svg>
  );
}

export function DocumentIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <path d="M6 3h9l4 4v14H6z" />
      <path d="M14 3v5h5M9 13h6M9 17h6" />
    </svg>
  );
}

export function ShieldCheckIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <path d="M9 12l2 2 4-5" />
      <path d="M12 3l7 3v5c0 5-3.5 8-7 10-3.5-2-7-5-7-10V6z" />
    </svg>
  );
}

export function DatabaseIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <ellipse cx="12" cy="6" rx="7" ry="3" />
      <path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6" />
      <path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" />
    </svg>
  );
}

export function CogIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19 12a7 7 0 0 0-.1-1.2l2-1.5-2-3.4-2.3 1a7 7 0 0 0-2-1.2L14.2 3h-4l-.4 2.7a7 7 0 0 0-2 1.2l-2.3-1-2 3.4 2 1.5a7 7 0 0 0 0 2.4l-2 1.5 2 3.4 2.3-1a7 7 0 0 0 2 1.2l.4 2.7h4l.4-2.7a7 7 0 0 0 2-1.2l2.3 1 2-3.4-2-1.5c.06-.4.1-.8.1-1.2z" />
    </svg>
  );
}

export function SearchIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4-4" />
    </svg>
  );
}

export function BellIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <path d="M18 9a6 6 0 1 0-12 0c0 6-2.5 7-2.5 7h17S18 15 18 9" />
      <path d="M10 20a2.2 2.2 0 0 0 4 0" />
    </svg>
  );
}

export function HelpIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...STROKE} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.5 9.5a2.5 2.5 0 1 1 3.4 2.3c-.8.3-.9 1-.9 1.7M12 17v.1" />
    </svg>
  );
}

export const ICONS = {
  grid: GridIcon,
  activity: ActivityIcon,
  trend: TrendIcon,
  shuffle: ShuffleIcon,
  triangleAlert: TriangleAlertIcon,
  cart: CartIcon,
  clock: ClockIcon,
  agent: AgentBoxIcon,
  document: DocumentIcon,
  shield: ShieldCheckIcon,
  database: DatabaseIcon,
  cog: CogIcon,
} as const;

export type IconName = keyof typeof ICONS;
