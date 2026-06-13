/**
 * SmartInv color tokens.
 *
 * Source of truth for every color used in the product. All values come from
 * the high-fidelity UI mock at `docs/smartinv-ui.html`. Components must not
 * reference raw hex — only token names — enforced by `pnpm lint:hex`.
 *
 * Semantic rule (AGENTS.md non-negotiable #8):
 *   `ai`        → violet, reserved for AI-generated content ONLY.
 *   `ok|warn|crit` → reserved for status states; never for AI.
 */

export const chrome = {
  DEFAULT: '#10161F',
  '2': '#161E2A',
  line: '#243040',
} as const;

export const surface = {
  DEFAULT: '#F4F6F8',
  card: '#FFFFFF',
  line: '#E3E8EE',
} as const;

/** Ink scale: text and foreground from strongest to lightest. */
export const ink = {
  DEFAULT: '#16212E',
  '2': '#5A6B7E',
  '3': '#8B99A9',
} as const;

/** Brand teal scale. */
export const teal = {
  DEFAULT: '#0E8C9C',
  dark: '#0A6B78',
  soft: '#E3F4F6',
} as const;

/** AI accent — RESERVED for AI-generated content. Do not use for status. */
export const ai = {
  DEFAULT: '#6D5AE6',
  soft: '#F0EDFD',
} as const;

export const ok = {
  DEFAULT: '#2E9E6B',
  soft: '#E5F5EE',
} as const;

export const warn = {
  DEFAULT: '#D98E1B',
  soft: '#FCF2DF',
} as const;

export const crit = {
  DEFAULT: '#D64545',
  soft: '#FBEAEA',
} as const;

/** Aggregate color palette consumed by the Tailwind theme. */
export const color = {
  chrome,
  surface,
  card: surface.card,
  line: surface.line,
  ink,
  teal,
  ai,
  ok,
  warn,
  crit,
} as const;

export type Color = typeof color;
