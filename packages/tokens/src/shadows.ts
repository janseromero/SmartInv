/**
 * SmartInv shadow tokens.
 *
 * The single contextual shadow from the mock — used for cards and panels.
 * Avoid adding more variants until at least three real surfaces actually
 * demand them.
 */

export const shadow = {
  card: '0 1px 2px rgba(22, 33, 46, 0.05), 0 4px 14px rgba(22, 33, 46, 0.05)',
  raised: '0 2px 4px rgba(22, 33, 46, 0.06), 0 10px 28px rgba(22, 33, 46, 0.08)',
} as const;

export type Shadow = typeof shadow;
