/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["'Geist'", "'Inter'", "system-ui", "sans-serif"],
        mono: ["'Geist Mono'", "monospace"],
      },
      colors: {
        surface: {
          DEFAULT: "#0f1117",
          raised: "#161b27",
          border: "#1e2535",
          muted: "#252d3d",
        },
        brand: {
          DEFAULT: "#3b82f6",
          dim: "#1d4ed8",
          glow: "#60a5fa",
        },
        risk: {
          low: "#22c55e",
          medium: "#f59e0b",
          high: "#ef4444",
          emergency: "#dc2626",
        },
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-up": "fadeUp 0.35s ease forwards",
        "fade-in": "fadeIn 0.2s ease forwards",
        "typing": "typing 1.4s steps(3, end) infinite",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        typing: {
          "0%, 100%": { content: "''" },
          "33%": { content: "'.'" },
          "66%": { content: "'..'" },
        },
      },
    },
  },
  plugins: [],
};
