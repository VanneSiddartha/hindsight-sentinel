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
        dark: {
          900: '#0B0F19',
          800: '#111827',
          700: '#1F2937',
          600: '#374151',
        },
        sentinel: {
          green: '#10B981',
          yellow: '#F59E0B',
          red: '#EF4444',
          accent: '#6366F1',
          cyan: '#06B6D4'
        }
      }
    },
  },
  plugins: [],
}
