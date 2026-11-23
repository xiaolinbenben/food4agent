import { categories as skillCategories, skills as skillCatalog } from "virtual:food4agent-skills";

export const repoUrl = "https://github.com/xiaolinbenben/food4agent";
export const siteOrigin = "https://food4agent.com";

export type SkillEntry = {
  name: string;
  summary: string;
  categoryId: string;
};

export type SkillCategory = {
  id: string;
  label: string;
};

export type McpEntry = {
  name: string;
  summary: string;
  command: string;
};

export const skills: SkillEntry[] = skillCatalog;
export const categories: SkillCategory[] = skillCategories;

export const mcps: McpEntry[] = [
  {
    name: "hello-world",
    summary: "提供 hello_world 工具，返回 hello world。",
    command: "command: python3\nargs: server.py\ncwd: /你的路径/food4agent/mcp/hello-world",
  },
];

export function siteSkillUrl(name: string) {
  return `${siteOrigin}/skills/${name}`;
}

export function githubMcpUrl(name: string) {
  return `${repoUrl}/mcp/${name}`;
}
