/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      colors: {
        background: "#F1FBFA",
        foreground: "#0E3A3D",
        secondary: "#5D8284",
        accent: "#FF5A3C",
        teal: "#0F9D8A",
        aqua: "#46C9BF",
        dark: "#10211F",
        metallic: "#AABFBE",
        border: "#D3E8E7",
      },
    },
  },
  plugins: [],
}