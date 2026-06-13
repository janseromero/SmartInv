/**
 * SmartInv typography tokens.
 *
 * Three font stacks, mapped directly to Tailwind's fontFamily:
 *   body    → IBM Plex Sans (UI text)
 *   mono    → IBM Plex Mono (IDs, codes, model versions)
 *   display → Space Grotesk (titles, hero text)
 *
 * All three are loaded via Google Fonts (see apps/web/app/layout.tsx).
 */

export const fontFamily = {
  body: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'] as const,
  mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'] as const,
  display: ['"Space Grotesk"', 'system-ui', 'sans-serif'] as const,
} as const;

/** Type scale in pixels, mapped to Tailwind text-* utilities where useful. */
export const fontSize = {
  xs: 11,
  sm: 12,
  base: 13.5,
  md: 14,
  lg: 16,
  xl: 18,
  '2xl': 22,
  '3xl': 27,
  display: 40,
} as const;

export type FontFamily = typeof fontFamily;
export type FontSize = typeof fontSize;
