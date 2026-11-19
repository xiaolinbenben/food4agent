import { useEffect, useState } from "react";
import { Check, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FAQAccordion } from "@/components/blocks/faq-section";
import { FooterSimple } from "@/components/blocks/footer-section";
import { HeroCentered } from "@/components/blocks/hero-section";
import { githubMcpUrl, mcps, repoUrl, siteOrigin, siteSkillUrl, skills, type SkillEntry } from "@/catalog";

function currentPath() {
  const path = window.location.pathname.replace(/\/+$/, "");
  return path || "/";
}

function skillNameFromPath(path: string) {
  const prefix = "/skills/";
  if (!path.startsWith(prefix)) return "";
  const name = path.slice(prefix.length);
  if (!name || name.includes("/")) return "";
  return decodeURIComponent(name);
}

export default function App() {
  const path = currentPath();
  const skillName = skillNameFromPath(path);
  const skill = skills.find((item) => item.name === skillName) ?? null;
  const [copied, setCopied] = useState("");

  useEffect(() => {
    const titles: Record<string, string> = {
      "/": "food4agent · 技能和 MCP",
      "/skills": "food4agent · 全部技能",
      "/mcp": "food4agent · 全部 MCP",
    };
    document.title = skill ? `food4agent · ${skill.name}` : (titles[path] ?? "food4agent");
  }, [path, skill]);

  async function copyText(key: string, value: string) {
    await navigator.clipboard.writeText(value);
    setCopied(key);
  }

  const known = path === "/" || path === "/skills" || path === "/mcp" || skill !== null;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <SiteHeader path={path} />
      <main>
        {path === "/" && <Home />}
        {path === "/skills" && <SkillCatalog copied={copied} onCopy={copyText} />}
        {skill && <SkillPage skill={skill} copied={copied} onCopy={copyText} />}
        {path === "/mcp" && <McpCatalog copied={copied} onCopy={copyText} />}
        {!known && <Missing />}
      </main>
    </div>
  );
}

function SiteHeader({ path }: { path: string }) {
  const links = [
    { href: "/skills", label: "技能" },
    { href: "/mcp", label: "MCP" },
  ];
  return (
    <header className="sticky top-0 z-20 border-b-3 border-foreground bg-background">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-3 md:px-8">
        <a href="/" className="text-lg font-black uppercase tracking-tight">
          food4agent
        </a>
        <nav className="flex items-center gap-5 text-sm font-bold uppercase">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className={path === link.href || path.startsWith(`${link.href}/`) ? "bg-primary px-2 text-primary-foreground" : undefined}
            >
              {link.label}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}

function Home() {
  return (
    <>
      <HeroCentered
        title="给 Agent 用的"
        titleHighlight="技能和 MCP"
        description="打开技能页，把地址发给 Agent 就可以安装。"
        primaryAction={{ label: "查看技能", href: "/skills" }}
        secondaryAction={{ label: "查看 MCP", href: "/mcp" }}
      />

      <section className="px-4 pb-8 md:px-8 lg:px-16">
        <div className="mx-auto grid max-w-6xl gap-6 md:grid-cols-2">
          <Card interactive>
            <a href="/skills" className="block">
              <CardHeader>
                <CardDescription>/skills</CardDescription>
                <CardTitle>技能</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">共 {skills.length} 个。点进去复制安装地址。</p>
              </CardContent>
            </a>
          </Card>
          <Card interactive>
            <a href="/mcp" className="block">
              <CardHeader>
                <CardDescription>/mcp</CardDescription>
                <CardTitle>MCP</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">共 {mcps.length} 个。点进去按页面上的命令启动。</p>
              </CardContent>
            </a>
          </Card>
        </div>
      </section>

      <section id="install" className="px-4 py-8 md:px-8 lg:px-16">
        <div className="mx-auto max-w-6xl border-3 border-foreground bg-card shadow-[4px_4px_0px_hsl(var(--shadow-color))]">
          <div className="space-y-4 p-6 md:p-8">
            <h2 className="text-2xl font-black tracking-tight md:text-3xl">把地址发给 Agent</h2>
            <p className="max-w-2xl text-muted-foreground">把技能名换到地址末尾。例如 hello-world。</p>
            <pre className="overflow-x-auto whitespace-pre-wrap break-all border-3 border-foreground bg-muted p-4 text-sm">{`${siteOrigin}/skills/<name>`}</pre>
          </div>
          <p className="border-t-3 border-foreground bg-muted px-6 py-4 text-sm text-muted-foreground md:px-8">
            技能会装到当前项目的 skills/&lt;name&gt;。同名目录已经存在时，先删掉再装。每个技能的地址在{" "}
            <a href="/skills" className="font-bold text-foreground underline">
              技能页
            </a>
            。
          </p>
        </div>
      </section>

      <FAQAccordion
        title="常见问题"
        items={[
          { question: "food4agent 是什么？", answer: "给 Agent 用的技能和 MCP。这个网站用来查看内容，以及复制安装地址。" },
          { question: "技能怎么安装？", answer: "打开技能页，复制 food4agent.com/skills/技能名，发给 Agent。技能会装进当前项目的 skills 目录。" },
          { question: "MCP 怎么使用？", answer: "打开 MCP 页，让 Agent 按上面的命令启动。代码更新后，重新启动 Agent。" },
          { question: "更新之后要重新安装吗？", answer: "技能要重新安装。项目里已经有同名目录时，先删掉再装。MCP 不用重装，重新启动 Agent 即可。" },
        ]}
      />
      <FooterSimple
        logo="food4agent"
        links={[
          { label: "技能", href: "/skills" },
          { label: "MCP", href: "/mcp" },
          { label: "仓库", href: repoUrl },
        ]}
        copyright="food4agent · 技能与 MCP"
      />
    </>
  );
}

function SkillCatalog({ copied, onCopy }: { copied: string; onCopy: (key: string, value: string) => void }) {
  return (
    <section className="px-4 py-16 md:px-8 lg:px-16">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 space-y-3">
          <p className="text-sm font-bold uppercase tracking-widest text-primary">/skills</p>
          <h1 className="text-3xl font-black tracking-tight md:text-5xl">全部技能</h1>
          <p className="max-w-3xl text-muted-foreground">复制地址发给 Agent。技能会装到当前项目里的同名目录。这个目录已经存在时，先删掉再装。</p>
        </div>
        <div className="grid gap-6">
          {skills.map((skill) => (
            <SkillCard key={skill.name} skill={skill} copied={copied} onCopy={onCopy} />
          ))}
        </div>
      </div>
    </section>
  );
}

function SkillPage({ skill, copied, onCopy }: { skill: SkillEntry; copied: string; onCopy: (key: string, value: string) => void }) {
  const url = siteSkillUrl(skill.name);
  return (
    <section className="px-4 py-16 md:px-8 lg:px-16">
      <div className="mx-auto max-w-6xl space-y-8">
        <div className="space-y-3">
          <p className="text-sm font-bold uppercase tracking-widest text-primary">
            <a href="/skills">全部技能</a>
          </p>
          <h1 className="text-3xl font-black tracking-tight md:text-5xl">{skill.name}</h1>
          <p className="max-w-3xl text-muted-foreground">{skill.summary}</p>
        </div>
        <Card>
          <CardHeader>
            <CardDescription>安装地址</CardDescription>
            <CardTitle className="normal-case">发给 Agent</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <pre className="overflow-x-auto whitespace-pre-wrap break-all border-3 border-foreground bg-muted p-4 text-sm">{url}</pre>
            <CopyButton copied={copied === skill.name} label="复制地址" onClick={() => onCopy(skill.name, url)} />
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

function SkillCard({ skill, copied, onCopy }: { skill: SkillEntry; copied: string; onCopy: (key: string, value: string) => void }) {
  const url = siteSkillUrl(skill.name);
  return (
    <Card id={skill.name}>
      <CardHeader>
        <CardDescription>food4agent.com/skills/{skill.name}</CardDescription>
        <CardTitle className="normal-case">
          <a href={`/skills/${skill.name}`}>{skill.name}</a>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-muted-foreground">{skill.summary}</p>
        <pre className="overflow-x-auto whitespace-pre-wrap break-all border-3 border-foreground bg-muted p-4 text-sm">{url}</pre>
        <CopyButton copied={copied === skill.name} label="复制地址" onClick={() => onCopy(skill.name, url)} />
      </CardContent>
    </Card>
  );
}

function McpCatalog({ copied, onCopy }: { copied: string; onCopy: (key: string, value: string) => void }) {
  return (
    <section className="px-4 py-16 md:px-8 lg:px-16">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 space-y-3">
          <p className="text-sm font-bold uppercase tracking-widest text-primary">/mcp</p>
          <h1 className="text-3xl font-black tracking-tight md:text-5xl">全部 MCP</h1>
          <p className="max-w-3xl text-muted-foreground">让 Agent 按下面的命令启动。cwd 换成你电脑上这份仓库里的对应目录。代码更新后，重新启动 Agent。</p>
        </div>
        <div className="grid gap-6">
          {mcps.map((mcp) => (
            <Card key={mcp.name} id={mcp.name}>
              <CardHeader>
                <CardDescription>mcp/{mcp.name}</CardDescription>
                <CardTitle className="normal-case">{mcp.name}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">{mcp.summary}</p>
                <pre className="overflow-x-auto whitespace-pre-wrap break-all border-3 border-foreground bg-muted p-4 text-sm">{mcp.command}</pre>
                <div className="flex flex-wrap gap-3">
                  <CopyButton copied={copied === `${mcp.name}:config`} label="复制启动命令" onClick={() => onCopy(`${mcp.name}:config`, mcp.command)} />
                  <Button variant="outline" asChild>
                    <a href={githubMcpUrl(mcp.name)}>打开目录</a>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

function Missing() {
  return (
    <section className="px-4 py-20 md:px-8">
      <div className="mx-auto max-w-3xl space-y-4">
        <h1 className="text-3xl font-black tracking-tight">没有这个页面</h1>
        <p className="text-muted-foreground">可以去看技能或 MCP。</p>
        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <a href="/skills">查看技能</a>
          </Button>
          <Button variant="outline" asChild>
            <a href="/mcp">查看 MCP</a>
          </Button>
        </div>
      </div>
    </section>
  );
}

function CopyButton({ copied, label, onClick, outline }: { copied: boolean; label: string; onClick: () => void; outline?: boolean }) {
  return (
    <Button variant={outline ? "outline" : "default"} onClick={() => void onClick()}>
      {copied ? <Check /> : <Copy />}
      {copied ? "已复制" : label}
    </Button>
  );
}
