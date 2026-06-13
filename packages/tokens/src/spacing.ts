/**
 * SmartInv spacing tokens.
 *
 * Pixel-based, mapped to Tailwind's spacing scale. We do not extend the
 * default Tailwind scale (0, 1, 2, 4, 8...) because most layouts use it
 * directly. The tokens below are the *named* contextual spaces from the UI
 * mock — used when a layout needs a meaning, not a number.
 */

export const space = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 48,
} as const;

export type Space = typeof space;
