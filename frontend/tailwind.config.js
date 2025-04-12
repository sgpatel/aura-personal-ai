/** @type {import('tailwindcss').Config} */
const config = { // Or module.exports = { depending on your project type
  content: [
    "./index.html", // Include the main HTML file
    "./src/**/*.{js,ts,jsx,tsx}", // Include all JS, TS, JSX, TSX files in the src folder
  ],
  darkMode: 'class', // Make sure dark mode is enabled via class strategy
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;