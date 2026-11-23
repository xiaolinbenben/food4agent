import { execFileSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import type { SkillCategory, SkillEntry } from "./src/catalog";

export type RegistryFile = { path: string; sha256: string; size: number };

export type RegistryManifest = { name: string; version: string; files: RegistryFile[] };

export type RegistryIndexEntry = {
  name: string;
  summary: string;
  categoryId: string;
  version: string;
  updated_at: string;
  file_count: number;
  size_bytes: number;
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

  let totalBytes = 0;
  const entries: RegistryIndexEntry[] = catalog.skills.map((skill) => {
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
    const size = manifestFiles.reduce((sum, file) => sum + file.size, 0);
    totalBytes += size;
    return {
      name: skill.name,
      summary: skill.summary,
      categoryId: skill.categoryId,
      version: manifest.version,
      updated_at: updatedAt.get(skill.name) ?? "",
      file_count: manifestFiles.length,
      size_bytes: size,
    };
  });

  const index: RegistryIndex = {
    schema: 1,
    generated_at: new Date().toISOString(),
    categories: catalog.categories,
    skills: entries,
  };
  fs.writeFileSync(path.join(registryDir, "skills.json"), JSON.stringify(index));
  return { count: entries.length, totalBytes };
}
