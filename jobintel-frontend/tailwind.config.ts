import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#0F1115",
          surface: "#161A21",
          elevated: "#1E232B"
        },
        border: {
          subtle: "#252B36",
          default: "#2F3642"
        },
        text: {
          primary: "#E6EAF0",
          secondary: "#A5ACB8",
          muted: "#6B7280"
        },
        accent: {
          primary: "#4F8EF7"
        }
      },
      borderRadius: {
        card: "10px"
      }
    },
  },
  plugins: [],
} satisfies Config
