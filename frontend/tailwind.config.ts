import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

// NIPAM brand system. Navy is the institutional base (~40%), green the action
// and identity colour (~30%), white (~20%) and silver/light grey (~10%).
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    container: { center: true, padding: { DEFAULT: "1rem", sm: "1.5rem", lg: "2rem" }, screens: { "2xl": "1280px" } },
    extend: {
      colors: {
        navy: {
          50: "#EEF4FA",
          100: "#D6E4F1",
          200: "#ADC8E2",
          300: "#7EA6CD",
          400: "#4A7FB0",
          500: "#1F5A8E",
          600: "#0C4A7D",
          700: "#063B66",
          800: "#052F52",
          900: "#04243F",
          950: "#021629",
          DEFAULT: "#063B66",
        },
        green: {
          50: "#EAF8F0",
          100: "#CDEFDB",
          200: "#9BDFB8",
          300: "#5FC98E",
          400: "#2BB06A",
          500: "#079447",
          600: "#067F3D", // AA-contrast shade used for text/buttons on white
          700: "#006B3C", // Deep Green
          800: "#045530",
          900: "#033F24",
          DEFAULT: "#079447",
        },
        silver: { DEFAULT: "#9AA0A6", light: "#D5D9DD", dark: "#5B6670" },
        surface: "#F5F8F7",
        border: "#E3E8EC",
        ring: "#079447",
        background: "#FFFFFF",
        foreground: "#0B1B2B",
        muted: { DEFAULT: "#F5F8F7", foreground: "#5B6670" },
        destructive: { DEFAULT: "#C0352B", foreground: "#FFFFFF" },
        warning: { DEFAULT: "#B45309", light: "#FEF3C7" },
      },
      fontFamily: {
        sans: ['"Inter Variable"', "system-ui", "sans-serif"],
        display: ['"Plus Jakarta Sans Variable"', '"Inter Variable"', "system-ui", "sans-serif"],
      },
      borderRadius: { xl: "0.875rem", "2xl": "1.125rem", "3xl": "1.5rem" },
      boxShadow: {
        card: "0 1px 2px rgba(6,59,102,0.06), 0 4px 16px -4px rgba(6,59,102,0.08)",
        lift: "0 2px 4px rgba(6,59,102,0.06), 0 16px 32px -8px rgba(6,59,102,0.18)",
      },
      keyframes: {
        "fade-up": { from: { opacity: "0", transform: "translateY(8px)" }, to: { opacity: "1", transform: "none" } },
        shimmer: { "100%": { transform: "translateX(100%)" } },
      },
      animation: {
        "fade-up": "fade-up 0.4s ease-out both",
      },
    },
  },
  plugins: [animate],
} satisfies Config;
