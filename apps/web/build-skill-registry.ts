import { execFileSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import type { SkillCategory, SkillEntry } from "./src/catalog";
import { zipStore } from "./zip-store.ts";

const discoverySchema = "https://schemas.agentskills.io/discovery/0.2.0/schema.json";

export type RegistryFile = { path: string; sha256: string; size: number };

export type RegistryManifest = { name: string; version: string; files: RegistryFile[] };

export type RegistryIndexEntry = {
  name: string;
  summary: string;
  categoryId: string;
  version: string;
  digest: string;
  updated_at: string;
  file_count: number;
  size_bytes: number;
};

export type DiscoverySkill = {
  name: string;
  type: "archive";
  description: string;
  url: string;
  digest: string;
};

export type RegistryIndex = {
  schema: 1;
  generated_at: string;
  categories: SkillCategory[];
  skills: RegistryIndexEntry[];
};

// 只发布 git 跟踪的文件，跳过以点开头的路径段，保证同一提交构建出相同版本。
export function listSkillFiles(repoRoot: string) {
  const output = execFileSync("git", ["ls-files", "-z", "--", "skills"], { cwd: repoRoot, maxBuffer: 64 * 1024 * 1024 });
  const bySkill = new Map<string, string[]>();
  for (const file of output.toString("utf8").split("\0")) {
    const parts = file.split("/");
    if (parts.length < 3 || parts.some((part) => part.startsWith("."))) continue;
    const [, name, ...rest] = parts;
    const list = bySkill.get(name) ?? [];
    list.push(rest.join("/"));
    bySkill.set(name, list);
  }
  for (const list of bySkill.values()) list.sort();
  return bySkill;
}

function readUpdatedAt(repoRoot: string) {
  const output = execFileSync("git", ["log", "--format=%x00%cI", "--name-only", "--", "skills"], {
    cwd: repoRoot,
    maxBuffer: 256 * 1024 * 1024,
  });
  const updatedAt = new Map<string, string>();
  for (const commit of output.toString("utf8").split("\0").slice(1)) {
    const [date, ...files] = commit.split("\n");
    for (const file of files) {
      const name = file.split("/")[1];
      if (file.startsWith("skills/") && name && !updatedAt.has(name)) updatedAt.set(name, date.trim());
    }
  }
  return updatedAt;
}

export function skillVersion(files: RegistryFile[]) {
  const hash = crypto.createHash("sha256");
  for (const file of files) hash.update(`${file.path}\0${file.sha256}\n`);
  return hash.digest("hex").slice(0, 12);
}

export function buildSkillRegistry(
  repoRoot: string,
  outDir: string,
  catalog: { skills: SkillEntry[]; categories: SkillCategory[] },
) {
  const files = listSkillFiles(repoRoot);
  const updatedAt = readUpdatedAt(repoRoot);
  const registryDir = path.join(outDir, "registry");
  fs.rmSync(registryDir, { recursive: true, force: true });
  fs.rmSync(path.join(outDir, ".well-known"), { recursive: true, force: true });
  fs.rmSync(path.join(outDir, "skills"), { recursive: true, force: true });

  let totalBytes = 0;
  const entries = catalog.skills.map((skill) => {
    const relativeFiles = files.get(skill.name);
    if (!relativeFiles?.includes("SKILL.md")) {
      throw new Error(`${skill.name}: git 没有跟踪 SKILL.md`);
    }
    const sourceDir = path.join(repoRoot, "skills", skill.name);
    const targetDir = path.join(registryDir, "skills", skill.name);
    const manifestFiles = relativeFiles.map((relative) => {
      const content = fs.readFileSync(path.join(sourceDir, relative));
      const target = path.join(targetDir, relative);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, content);
      return { path: relative, sha256: crypto.createHash("sha256").update(content).digest("hex"), size: content.length };
    });
    const manifest: RegistryManifest = { name: skill.name, version: skillVersion(manifestFiles), files: manifestFiles };
    fs.writeFileSync(path.join(targetDir, "manifest.json"), JSON.stringify(manifest));
    const packed = zipStore(manifestFiles.map((file) => ({
      path: file.path,
      data: fs.readFileSync(path.join(sourceDir, file.path)),
    })));
    const archiveName = `${skill.name}.zip`;
    const archiveDir = path.join(outDir, ".well-known", "agent-skills");
    fs.mkdirSync(archiveDir, { recursive: true });
    fs.writeFileSync(path.join(archiveDir, archiveName), packed.archive);
    const discoverySkill: DiscoverySkill = {
      name: skill.name,
      type: "archive",
      description: skill.summary || skill.name,
      url: `/.well-known/agent-skills/${archiveName}`,
      digest: packed.digest,
    };
    const skillIndexDir = path.join(outDir, "skills", skill.name, ".well-known", "agent-skills");
    fs.mkdirSync(skillIndexDir, { recursive: true });
    fs.writeFileSync(path.join(skillIndexDir, "index.json"), JSON.stringify({
      $schema: discoverySchema,
      skills: [discoverySkill],
    }));
    const size = manifestFiles.reduce((sum, file) => sum + file.size, 0);
    totalBytes += size;
    return {
      name: skill.name,
      summary: skill.summary,
      categoryId: skill.categoryId,
      version: manifest.version,
      digest: packed.digest,
      updated_at: updatedAt.get(skill.name) ?? "",
      file_count: manifestFiles.length,
      size_bytes: size,
      discovery: discoverySkill,
    };
  });

  const skills = entries.map(({ discovery: _discovery, ...entry }) => entry);
  const index: RegistryIndex = {
    schema: 1,
    generated_at: new Date().toISOString(),
    categories: catalog.categories,
    skills,
  };
  fs.writeFileSync(path.join(registryDir, "skills.json"), JSON.stringify(index));
  const discoveryDir = path.join(outDir, ".well-known", "agent-skills");
  fs.mkdirSync(discoveryDir, { recursive: true });
  fs.writeFileSync(path.join(discoveryDir, "index.json"), JSON.stringify({
    $schema: discoverySchema,
    skills: entries.map((entry) => entry.discovery),
  }));
  return { count: entries.length, totalBytes };
}

const trackedSkills = new Map<string, { at: number; files: Map<string, string[]> }>();

function trackedSkillFiles(repoRoot: string) {
  const cached = trackedSkills.get(repoRoot);
  if (cached && Date.now() - cached.at < 2000) return cached.files;
  const files = listSkillFiles(repoRoot);
  trackedSkills.set(repoRoot, { at: Date.now(), files });
  return files;
}

function registryType(rel: string) {
  if (rel.endsWith(".json")) return "application/json; charset=utf-8";
  if (rel.endsWith(".md")) return "text/markdown; charset=utf-8";
  if (/\.(py|txt|ts|js|sh|yml|yaml)$/.test(rel)) return "text/plain; charset=utf-8";
  return "application/octet-stream";
}

export function readRegistryAsset(repoRoot: string, requestPath: string): { body: Buffer; type: string } | null {
  const prefix = "/registry/skills/";
  if (!requestPath.startsWith(prefix)) return null;
  const rest = requestPath.slice(prefix.length);
  if (!rest || rest.split("/").some((part) => part === "" || part === "." || part === "..")) return null;
  const slash = rest.indexOf("/");
  const name = slash === -1 ? rest : rest.slice(0, slash);
  const rel = slash === -1 ? "" : rest.slice(slash + 1);
  const files = trackedSkillFiles(repoRoot).get(name);
  if (!files) return null;
  if (rel === "manifest.json") {
    const manifestFiles = files.map((file) => {
      const content = fs.readFileSync(path.join(repoRoot, "skills", name, file));
      return { path: file, sha256: crypto.createHash("sha256").update(content).digest("hex"), size: content.length };
    });
    const manifest: RegistryManifest = { name, version: skillVersion(manifestFiles), files: manifestFiles };
    return { body: Buffer.from(JSON.stringify(manifest)), type: "application/json; charset=utf-8" };
  }
  if (!files.includes(rel)) return null;
  return { body: fs.readFileSync(path.join(repoRoot, "skills", name, rel)), type: registryType(rel) };
}
