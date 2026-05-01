import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          DEFAULT: '#2D5016',
          light: '#4a7a23',
          pale: '#8db86c',
          50: '#f0f7e6',
          100: '#d6ebb3',
          200: '#b3d980',
          300: '#8dc650',
          400: '#67b330',
          500: '#4a9020',
          600: '#2D5016',
          700: '#1e3610',
          800: '#0f1b08',
          900: '#060d04',
        },
        cream: '#F5F0E8',
        parchment: '#EDE8DC',
        earth: '#6B4D2A',
        amber: {
          DEFAULT: '#C4870A',
          light: '#D4A017',
          pale: '#F0C842',
        },
        sky: {
          DEFAULT: '#6B94A8',
          light: '#9DBFCF',
          pale: '#D4E8F0',
        },
        bark: '#8B6914',
      },
      fontFamily: {
        serif: ['Playfair Display', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'paper-texture': "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E\")",
      },
      boxShadow: {
        card: '2px 4px 12px rgba(45, 80, 22, 0.12), 0 1px 3px rgba(0,0,0,0.08)',
        'card-hover': '4px 8px 24px rgba(45, 80, 22, 0.18), 0 2px 6px rgba(0,0,0,0.12)',
        'card-lifted': '6px 12px 32px rgba(45, 80, 22, 0.22), 0 4px 8px rgba(0,0,0,0.15)',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-4px)' },
        },
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        breathe: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.2)' },
        },
      },
      animation: {
        float: 'float 3s ease-in-out infinite',
        'fade-up': 'fade-up 0.5s ease-out forwards',
        breathe: 'breathe 8s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};

export default config;
