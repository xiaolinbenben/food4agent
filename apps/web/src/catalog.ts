export const repoUrl = "https://github.com/xiaolinbenben/food4agent";
export const siteOrigin = "https://food4agent.com";

export type SkillEntry = {
  name: string;
  summary: string;
};

export type McpEntry = {
  name: string;
  summary: string;
  command: string;
};

export const skills: SkillEntry[] = [
  { name: "hello-world", summary: "运行 scripts/hello.py，输出 hello world。" },
  { name: "terln-image-gen", summary: "用 gpt-image-2 生成或编辑图片。" },
  { name: "get-amazon-image", summary: "获取 Amazon 商品图片并保存到本地。" },
  { name: "print-fission", summary: "先读取印花的共同元素，再逐张改写风格和细节。" },
  { name: "listing", summary: "读取任务目录 input/ 的商品资料，生成 output/listing.xlsx。" },
];

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
