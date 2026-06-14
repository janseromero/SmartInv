import { color, fontFamily, fontSize, radius, shadow, space } from '@smartinv/tokens';
import type { Config } from 'tailwindcss';

/**
 * Tailwind theme for the ui-web package (used by Ladle). Mirrors the app's
 * token mapping so components render identically in isolation and in the app.
 */
const config: Config = {
  content: ['./src/**/*.{ts,tsx}', './.ladle/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ...color,
        surface: color.surface.DEFAULT,
        card: color.surface.card,
        line: color.surface.line,
      },
      borderRadius: Object.fromEntries(Object.entries(radius).map(([k, v]) => [k, `${v}px`])),
      spacing: Object.fromEntries(Object.entries(space).map(([k, v]) => [k, `${v}px`])),
      fontFamily: {
        body: [...fontFamily.body],
        mono: [...fontFamily.mono],
        display: [...fontFamily.display],
        sans: [...fontFamily.body],
      },
      fontSize: Object.fromEntries(Object.entries(fontSize).map(([k, v]) => [k, `${v}px`])),
      boxShadow: shadow,
    },
  },
  plugins: [],
};

export default config;
