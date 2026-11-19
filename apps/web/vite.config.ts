import path from "node:path";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { readSkillCatalog } from "./read-skill-catalog";

function food4agentSkills(): Plugin {
  const id = "virtual:food4agent-skills";
  const resolved = `\0${id}`;
  return {
    name: "food4agent-skills",
    resolveId(source) {
      if (source === id) return resolved;
    },
    load(source) {
      if (source !== resolved) return null;
      const skills = readSkillCatalog(path.resolve(__dirname, "../.."));
      return `export const skills = ${JSON.stringify(skills)};`;
    },
  };
}

export default defineConfig({
  base: "/",
  plugins: [food4agentSkills(), react(), tailwindcss()],
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
