import type { Config } from 'tailwindcss';

// Token values are wired in task E1.3 (consumes @smartinv/tokens).
// This minimal placeholder keeps `tailwindcss` happy and the build green.
const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    '../../packages/ui-web/src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
