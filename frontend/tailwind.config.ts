import type { Config } from 'tailwindcss';
import defaultTheme from 'tailwindcss/defaultTheme';

const config: Config = {
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Space Grotesk"', ...defaultTheme.fontFamily.sans],
        mono: ['"JetBrains Mono"', ...defaultTheme.fontFamily.mono],
      },
      colors: {
        midnight: '#0B1221',
        twilight: '#151F38',
        aurora: '#4AE3B5',
        corail: '#FF7C6E',
        mist: '#B4C7FF',
      },
      boxShadow: {
        panel: '0 20px 80px -32px rgba(6, 15, 40, 0.55)',
      },
    },
  },
  plugins: [],
};

export default config;
