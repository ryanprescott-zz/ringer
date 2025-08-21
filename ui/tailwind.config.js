/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ringer-blue': '#4a90a4',
        'ringer-dark-blue': '#2c5f75',
        'ringer-blue': '#4a90a4',
        'ringer-dark-blue': '#2c5f75',
        'table-header': '#d1d5db',
        'table-selected': '#bfdbfe',
      }
    },
  },
  plugins: [],
}
