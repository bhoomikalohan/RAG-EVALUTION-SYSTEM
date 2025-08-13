/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'chat-dark': '#343541',
        'chat-response': '#444654',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
