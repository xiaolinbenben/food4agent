import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  base: "/",
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: 3000,
    host: "0.0.0.0",
    proxy: {
      "/api": "http://127.0.0.1:8888",
      "/healthz": "http://127.0.0.1:8888",
    },
  },
  build: {
    outDir: "../server/web/dist/public",
    emptyOutDir: true,
  },
});
