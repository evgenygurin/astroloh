/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fefce8',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        dark: {
          50: '#1e1e2e',
          100: '#181825',
          200: '#11111b',
          300: '#0f0f19',
          400: '#0d0d14',
          500: '#0a0a0f',
          600: '#08080c',
          700: '#06060a',
          800: '#040407',
          900: '#020204',
        },
        mystical: {
          purple: '#6366f1',
          gold: '#fbbf24',
          silver: '#e5e7eb',
          cosmic: '#1e1b4b',
        }
      },
      fontFamily: {
        'mystical': ['Cinzel', 'serif'],
        'body': ['Inter', 'sans-serif'],
      },
      backgroundImage: {
        'cosmic': 'linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%)',
        'golden': 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%)',
        'mystical-radial': 'radial-gradient(ellipse at center, #1e1b4b 0%, #0a0a0f 70%)',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'planet-orbit': 'orbit 20s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        orbit: {
          '0%': { transform: 'rotate(0deg) translateX(100px) rotate(0deg)' },
          '100%': { transform: 'rotate(360deg) translateX(100px) rotate(-360deg)' },
        }
      }
    },
  },
  plugins: [],
}