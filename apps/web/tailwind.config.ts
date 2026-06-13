import { color, fontFamily, fontSize, radius, shadow, space } from '@smartinv/tokens';
import type { Config } from 'tailwindcss';

/**
 * Tailwind theme wired to @smartinv/tokens.
 *
 * Components must reference token names (e.g. `bg-teal`, `text-ink-2`,
 * `bg-ai-soft`, `rounded-md`, `shadow-card`) — never raw hex literals.
 * The `pnpm lint:hex` check enforces this.
 */
const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    '../../packages/ui-web/src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        ...color,
        // Flatten the `surface` family so `bg-surface`, `bg-card`, `border-line`
        // read naturally without the surface- prefix.
        surface: color.surface.DEFAULT,
        card: color.surface.card,
        line: color.surface.line,
      },
      borderRadius: Object.fromEntries(
        Object.entries(radius).map(([k, v]) => [k === 'DEFAULT' ? 'DEFAULT' : k, `${v}px`]),
      ),
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
