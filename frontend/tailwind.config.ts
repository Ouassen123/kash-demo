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
        knowledge: '#4AE3B5',
        abilities: '#8E7CFF',
        skills: '#FFB347',
        habits: '#6FB1FC',
        intelligence: '#FF7C6E',
      },
      boxShadow: {
        panel: '0 20px 80px -32px rgba(6, 15, 40, 0.55)',
        glow: '0 0 24px -4px rgba(91, 129, 255, 0.45)',
        'glow-aurora': '0 0 24px -4px rgba(74, 227, 181, 0.4)',
        'glow-corail': '0 0 24px -4px rgba(255, 124, 110, 0.4)',
      },
      backgroundImage: {
        'gradient-knowledge': 'linear-gradient(135deg, #4AE3B5, #178F66)',
        'gradient-abilities': 'linear-gradient(135deg, #8E7CFF, #4C3BCE)',
        'gradient-skills': 'linear-gradient(135deg, #FFB347, #FF7C6E)',
        'gradient-habits': 'linear-gradient(135deg, #6FB1FC, #365CFF)',
        'gradient-intelligence': 'linear-gradient(135deg, #FF7C6E, #C44569)',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in': {
          '0%': { opacity: '0', transform: 'translateX(-12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 12px -2px rgba(91,129,255,0.3)' },
          '50%': { boxShadow: '0 0 24px -2px rgba(91,129,255,0.6)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.4s ease-out',
        'slide-in': 'slide-in 0.3s ease-out',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};

export default config;
