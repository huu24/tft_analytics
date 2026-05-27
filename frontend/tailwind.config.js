/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        dark: {
          900: "#0a0e1a",
          800: "#0f1524",
          700: "#151d30",
          600: "#1c2640",
        },
        gold: "#c8aa6e",
        teal: "#0ac8b9",
      },
    },
  },
  plugins: [],
};
