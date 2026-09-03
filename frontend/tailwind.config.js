/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        matrix: {
          bg: '#050507',
          surface: '#0c0d12',
          card: '#10121a',
          cardHover: '#141722',
          border: '#1a1e2b',
          borderGlow: 'rgba(16, 185, 129, 0.25)',
          emerald: '#10b981',
          lime: '#84cc16',
          cyan: '#06b6d4',
          muted: '#64748b',
        }
      },
      boxShadow: {
        'matrix-glow': '0 0 20px -3px rgba(16, 185, 129, 0.25)',
        'matrix-glow-sm': '0 0 10px -2px rgba(16, 185, 129, 0.2)',
        'matrix-glow-lg': '0 0 30px -5px rgba(16, 185, 129, 0.35)',
        'rose-glow': '0 0 20px -3px rgba(244, 63, 94, 0.25)',
        'amber-glow': '0 0 20px -3px rgba(245, 158, 11, 0.25)',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      }
    },
  },
  plugins: [],
  darkMode: 'class',
}
