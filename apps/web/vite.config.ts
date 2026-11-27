import path from "node:path";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { readSkillCatalog } from "./read-skill-catalog";
import { buildSkillRegistry, readRegistryAsset } from "./build-skill-registry";
import { parseConsolePath } from "./src/console/paths";

const repoRoot = path.resolve(__dirname, "../..");

function food4agentSkills(): Plugin {
  const id = "virtual:food4agent-skills";
  const resolved = `\0${id}`;
  let outDir = "";
  let isBuild = false;
  return {
    name: "food4agent-skills",
    resolveId(source) {
      if (source === id) return resolved;
    },
    load(source) {
      if (source !== resolved) return null;
      const { skills, categories } = readSkillCatalog(repoRoot);
      return `export const skills = ${JSON.stringify(skills)};\nexport const categories = ${JSON.stringify(categories)};`;
    },
    configResolved(config) {
      outDir = path.resolve(config.root, config.build.outDir);
      isBuild = config.command === "build";
    },
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const pathname = decodeURIComponent((req.url ?? "").split("?")[0] ?? "");
        if (!pathname.startsWith("/registry/skills/")) {
          next();
          return;
        }
        try {
          const asset = readRegistryAsset(repoRoot, pathname);
          if (!asset) {
            res.statusCode = 404;
            res.setHeader("Content-Type", "text/plain; charset=utf-8");
            res.end("not found");
            return;
          }
          res.setHeader("Content-Type", asset.type);
          res.setHeader("Cache-Control", "no-cache");
          res.end(asset.body);
        } catch {
          res.statusCode = 404;
          res.setHeader("Content-Type", "text/plain; charset=utf-8");
          res.end("not found");
        }
      });
    },
    closeBundle() {
      if (!isBuild) return;
      const { count, totalBytes } = buildSkillRegistry(repoRoot, outDir, readSkillCatalog(repoRoot));
      this.info(`registry: ${count} 个技能，${(totalBytes / 1024 / 1024).toFixed(1)} MB`);
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
      "^/skill/[^/]+$": "http://127.0.0.1:8888",
      "^/[a-z0-9][a-z0-9-]{0,31}/skills": {
        target: "http://127.0.0.1:8888",
        bypass(req) {
          const pathname = (req.url ?? "").split("?")[0];
          if (parseConsolePath(pathname)) return pathname;
        },
      },
    },
  },
  build: {
    outDir: "../server/web/dist/public",
    emptyOutDir: true,
  },
});
