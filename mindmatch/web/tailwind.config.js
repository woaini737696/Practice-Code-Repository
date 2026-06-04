/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#8B5CF6',
          light: '#A78BFA',
          dark: '#7C3AED',
        },
        secondary: {
          DEFAULT: '#06B6D4',
          light: '#22D3EE',
        },
        accent: {
          DEFAULT: '#F59E0B',
          light: '#FBBF24',
        },
        background: {
          primary: '#0F0A1F',
          secondary: '#1A1033',
          card: 'rgba(139, 92, 246, 0.1)',
          glass: 'rgba(255, 255, 255, 0.05)',
        },
        text: {
          primary: '#F8FAFC',
          secondary: '#CBD5E1',
          muted: '#64748B',
        }
      },
      fontFamily: {
        sans: ['Noto Sans SC', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'night-sky': 'linear-gradient(to bottom, #0F0A1F, #1A1033)',
        'aurora': 'linear-gradient(135deg, #8B5CF6, #06B6D4)',
      }
    },
  },
  plugins: [],
}
