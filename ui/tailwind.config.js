/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'prospector-blue': '#4a90a4',
        'prospector-dark-blue': '#2c5f75',
      }
    },
  },
  plugins: [],
}
