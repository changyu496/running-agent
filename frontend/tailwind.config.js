/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0d9488',
          hover: '#0f766e',
          light: '#f0fdfa',
        },
        accent: {
          DEFAULT: '#b45309',
          light: '#fffbeb',
        },
      },
    },
  },
  plugins: [],
}
