/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      colors: {
        surface: {
          DEFAULT: '#0b0d11',
          secondary: '#12151c',
          card: '#1a1e27',
          input: '#0f1219',
        },
        border: '#2a2f3d',
        accent: {
          DEFAULT: '#6c5ce7',
          hover: '#7f6ff0',
          glow: 'rgba(108, 92, 231, 0.3)',
        },
        green: {
          DEFAULT: '#00d68f',
          glow: 'rgba(0, 214, 143, 0.2)',
        },
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}
