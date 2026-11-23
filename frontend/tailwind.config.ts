import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          obsidian: "#050B14",
          navy: "#0B1329",
          "navy-light": "#131F3F",
          electric: "#0055FF",
          "electric-hover": "#0043CC",
          cyan: "#38BDF8",
          neon: "#00E5BE",
          slate: "#94A3B8",
          muted: "#64748B",
          pureWhite: "#FFFFFF",
        },
      },
      fontFamily: {
        sans: ["var(--font-jakarta)", "Inter", "sans-serif"],
        brand: ["var(--font-outfit)", "Plus Jakarta Sans", "sans-serif"],
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "signature-gradient": "linear-gradient(135deg, #050B14 0%, #0B1329 50%, #0055FF 100%)",
        "btn-gradient": "linear-gradient(135deg, #0B1329 0%, #0055FF 100%)",
        "headline-gradient": "linear-gradient(135deg, #0055FF 0%, #38BDF8 50%, #00E5BE 100%)",
      },
      boxShadow: {
        "electric-glow": "0 0 35px rgba(0, 85, 255, 0.4)",
        "electric-sm": "0 0 15px rgba(0, 85, 255, 0.3)",
        glass: "0 20px 50px rgba(5, 11, 20, 0.7)",
      },
      animation: {
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        float: "float 6s ease-in-out infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
