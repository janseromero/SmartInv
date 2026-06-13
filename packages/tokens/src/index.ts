/**
 * SmartInv design tokens.
 *
 * Single source of truth for colors, spacing, typography, radii, and shadows.
 * Consumed by Tailwind (apps/web/tailwind.config.ts) and any future native
 * design system. Components must reference token names, never raw hex —
 * enforced by `pnpm lint:hex`.
 *
 * @see ../README.md for usage.
 */

export {
  ai,
  chrome,
  color,
  crit,
  ink,
  ok,
  surface,
  teal,
  warn,
} from './colors.js';
export type { Color } from './colors.js';

export { space } from './spacing.js';
export type { Space } from './spacing.js';

export { radius } from './radii.js';
export type { Radius } from './radii.js';

export { fontFamily, fontSize } from './typography.js';
export type { FontFamily, FontSize } from './typography.js';

export { shadow } from './shadows.js';
export type { Shadow } from './shadows.js';

export { semantic } from './semantic.js';
export type { Semantic } from './semantic.js';
