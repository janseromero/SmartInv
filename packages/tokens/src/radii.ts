/**
 * SmartInv border-radius tokens.
 *
 * Values from the UI mock:
 *   --r: 10px       → md (cards, panels)
 *   --r-sm: 7px     → sm (inputs, small chips)
 */

export const radius = {
  none: 0,
  sm: 7,
  DEFAULT: 10,
  md: 10,
  lg: 14,
  pill: 9999,
} as const;

export type Radius = typeof radius;
