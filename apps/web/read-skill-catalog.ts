import fs from "node:fs";
import path from "node:path";
import type { SkillCategory, SkillEntry } from "./src/catalog";

type CategoryDefinition = SkillCategory & { skills: string[] };

const blockIndicator = /^(?:>|\|)[+-]?\d*$/;

export function readSkillCatalog(repoRoot: string): { skills: SkillEntry[]; categories: SkillCategory[] } {
  const skillsDir = path.join(repoRoot, "skills");
  const names = fs
    .readdirSync(skillsDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort((left, right) => left.localeCompare(right));

  const definitions: CategoryDefinition[] = JSON.parse(fs.readFileSync(path.join(skillsDir, "categories.json"), "utf8"));
  if (!Array.isArray(definitions)) {
    throw new Error("skills/categories.json: 分类清单必须是数组");
  }
  const knownNames = new Set(names);
  const categoryIds = new Set<string>();
  const assignments = new Map<string, string>();
  const errors: string[] = [];
  for (const category of definitions) {
    if (
      !category || typeof category.id !== "string" || !/^[a-z][a-z0-9-]*$/.test(category.id) ||
      typeof category.label !== "string" || !category.label.trim() ||
      !Array.isArray(category.skills) || category.skills.some((name) => typeof name !== "string" || !name)
    ) {
      throw new Error("skills/categories.json: 每个分类必须有有效的 id、label 和 skills 名称数组");
    }
    if (categoryIds.has(category.id)) errors.push(`分类标识重复: ${category.id}`);
    categoryIds.add(category.id);
    for (const name of category.skills) {
      if (!knownNames.has(name)) errors.push(`引用不存在的技能: ${name} (${category.id})`);
      if (assignments.has(name)) errors.push(`重复归类: ${name} (${assignments.get(name)}, ${category.id})`);
      assignments.set(name, category.id);
    }
  }
  for (const name of names) {
    if (!assignments.has(name)) errors.push(`缺少归类: ${name}`);
  }
  if (errors.length) throw new Error(`skills/categories.json:\n${errors.join("\n")}`);

  const skills = names.map((dirName) => {
    const file = path.join(skillsDir, dirName, "SKILL.md");
    const text = fs.readFileSync(file, "utf8").replace(/^\uFEFF/, "");
    const frontmatter = readFrontmatter(text, dirName);
    const name = readName(frontmatter, dirName);
    if (name !== dirName) {
      throw new Error(`${dirName}: frontmatter name 是 ${name}`);
    }
    return { name, summary: readDescription(frontmatter, dirName), categoryId: assignments.get(name)! };
  });
  const categories = definitions.filter((category) => category.skills.length > 0).map(({ id, label }) => ({ id, label }));
  return { skills, categories };
}

function readFrontmatter(text: string, skillName: string) {
  const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) {
    throw new Error(`${skillName}: SKILL.md 缺少 frontmatter`);
  }
  return match[1];
}

function readName(frontmatter: string, skillName: string) {
  const match = frontmatter.match(/^name:\s*(.*)$/m);
  if (!match || !match[1].trim()) {
    throw new Error(`${skillName}: 缺少 name`);
  }
  return unquoteLine(match[1].trim());
}

function readDescription(frontmatter: string, skillName: string) {
  const lines = frontmatter.split(/\r?\n/);
  const index = lines.findIndex((line) => line.startsWith("description:"));
  if (index < 0) {
    throw new Error(`${skillName}: 缺少 description`);
  }
  const value = lines[index].slice("description:".length).replace(/^ /, "");
  const indicator = value.trim();
  let summary: string;
  if (indicator === "" || blockIndicator.test(indicator)) {
    summary = collectIndented(lines, index + 1).join(" ");
  } else if (indicator.startsWith("'") || indicator.startsWith('"')) {
    summary = readQuoted(lines, index, value, skillName);
  } else {
    summary = [indicator, ...collectIndented(lines, index + 1)].join(" ");
  }
  summary = summary.replace(/\s+/g, " ").trim();
  if (!summary) {
    throw new Error(`${skillName}: description 为空`);
  }
  return summary;
}

function collectIndented(lines: string[], start: number) {
  const parts: string[] = [];
  for (let index = start; index < lines.length; index += 1) {
    const line = lines[index];
    if (line.trim() === "") {
      continue;
    }
    if (!/^\s/.test(line)) {
      break;
    }
    parts.push(line.trim());
  }
  return parts;
}

function readQuoted(lines: string[], index: number, value: string, skillName: string) {
  const quote = value.trimStart()[0];
  let text = "";
  let closed = false;
  for (let lineIndex = index; lineIndex < lines.length && !closed; lineIndex += 1) {
    const line = lineIndex === index ? value.trimStart() : lines[lineIndex].trim();
    let column = lineIndex === index ? 1 : 0;
    while (column < line.length) {
      const char = line[column];
      if (quote === "'" && char === "'" && line[column + 1] === "'") {
        text += "'";
        column += 2;
        continue;
      }
      if (char === quote) {
        closed = true;
        break;
      }
      if (quote === '"' && char === "\\") {
        const next = line[column + 1];
        text += next === undefined ? "" : next === "n" || next === "t" ? " " : next;
        column += next === undefined ? 1 : 2;
        continue;
      }
      text += char;
      column += 1;
    }
    if (!closed) {
      text += " ";
    }
  }
  if (!closed) {
    throw new Error(`${skillName}: description 引号没有结束`);
  }
  return text;
}

function unquoteLine(value: string) {
  if (
    (value.startsWith('"') && value.endsWith('"') && value.length >= 2) ||
    (value.startsWith("'") && value.endsWith("'") && value.length >= 2)
  ) {
    return value.slice(1, -1);
  }
  return value;
}
