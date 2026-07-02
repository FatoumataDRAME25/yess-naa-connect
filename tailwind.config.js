/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        'yn-green-dark':  '#1A3A0A',
        'yn-green':       '#2D5A16',
        'yn-green-light': '#7DBD48',
        'yn-green-pale':  '#D4EDB8',
        'yn-terracotta':  '#C85A1A',
        'yn-gold':        '#D4A017',
        'yn-ivory':       '#F7F3ED',
        'yn-gray':        '#6B7280',
      },
      fontFamily: {
        'heading': ['Poppins', 'Sora', 'sans-serif'],
        'body':    ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
