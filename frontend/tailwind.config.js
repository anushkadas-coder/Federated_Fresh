/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: '#050505',
        panel: '#0f0f0f',
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'), // <-- SIRF YEH LINE ADD KARNI HAI
  ],
}