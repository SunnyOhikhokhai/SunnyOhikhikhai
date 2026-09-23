import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

const API = process.env.NIPAM_API_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: API, changeOrigin: false },
      "/uploads": { target: API },
      "/sitemap.xml": { target: API },
    },
  },
  preview: {
    port: 4173,
    proxy: { "/api": { target: API }, "/uploads": { target: API }, "/sitemap.xml": { target: API } },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          charts: ["recharts"],
          markdown: ["react-markdown"],
        },
      },
    },
  },
  plugins: [
    react(),
    VitePWA({
      registerType: "prompt",
      includeAssets: ["favicon.svg", "favicon.ico", "apple-touch-icon.png", "brand/*.svg", "robots.txt"],
      manifest: {
        id: "/",
        name: "NIPAM — Non-Indigenes for Philip Aduda Movement",
        short_name: "NIPAM",
        description:
          "A digital community connecting residents, sharing information and facilitating constructive civic engagement across the FCT.",
        theme_color: "#063B66",
        background_color: "#063B66",
        display: "standalone",
        orientation: "portrait-primary",
        start_url: "/?source=pwa",
        scope: "/",
        lang: "en-NG",
        categories: ["news", "social", "government"],
        icons: [
          { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
          { src: "/icons/maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
        shortcuts: [
          { name: "Our Record", url: "/our-record", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] },
          { name: "Events", url: "/events", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] },
          { name: "Dashboard", url: "/dashboard", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] },
        ],
      },
      workbox: {
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/api\//, /^\/uploads\//, /^\/sitemap\.xml$/],
        globPatterns: ["**/*.{js,css,html,svg,png,ico,woff2}"],
        globIgnores: ["**/icons/splash-*.png", "**/og-image.png"],
        runtimeCaching: [
          {
            // Selected public content is available offline (network first).
            urlPattern: ({ url }) =>
              /^\/api\/(home|meta|area-councils|projects|news|events|announcements)(\/|$|\?)/.test(url.pathname),
            handler: "NetworkFirst",
            options: {
              cacheName: "nipam-public-content",
              networkTimeoutSeconds: 4,
              expiration: { maxEntries: 150, maxAgeSeconds: 60 * 60 * 24 * 7 },
              cacheableResponse: { statuses: [200] },
            },
          },
          {
            urlPattern: ({ url }) => url.pathname.startsWith("/uploads/"),
            handler: "CacheFirst",
            options: { cacheName: "nipam-media", expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 30 } },
          },
        ],
      },
    }),
  ],
});
