import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: "#17104A",
          deep: "#100A36",
          indigo: "#1C165C",
          cyan: "#00BFF3",
          bright: "#10D7FF",
          soft: "#F5F7FB",
          lilac: "#ECEAF7",
          border: "#D7D9E3",
          muted: "#6F7485"
        },
        state: {
          success: "#0B8F6A",
          warning: "#B7791F",
          danger: "#B42318",
          info: "#0E7FD8"
        }
      },
      boxShadow: {
        panel: "0 18px 45px rgba(23, 16, 74, 0.10)",
        cyan: "0 0 0 1px rgba(0, 191, 243, .18), 0 18px 45px rgba(0, 191, 243, .12)"
      },
      backgroundImage: {
        "vf-radial": "radial-gradient(circle at 20% 20%, rgba(0,191,243,.22), transparent 28%), radial-gradient(circle at 80% 0%, rgba(23,16,74,.18), transparent 26%)",
        "vf-grid": "linear-gradient(rgba(23,16,74,.06) 1px, transparent 1px), linear-gradient(90deg, rgba(23,16,74,.06) 1px, transparent 1px)"
      }
    }
  },
  plugins: []
};
export default config;
