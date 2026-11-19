import { useEffect, useState } from "react";
import { Check, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FAQAccordion } from "@/components/blocks/faq-section";
import { FooterSimple } from "@/components/blocks/footer-section";
import { HeroCentered } from "@/components/blocks/hero-section";
import { githubMcpUrl, githubSkillUrl, localSkillPath, mcps, repoUrl, skills } from "@/catalog";

const steps = [
  { index: "01", title: "选一条路径", description: "GitHub 链接，或本机 food4agent 仓库里的目录。两条路径是同一份内容。" },
  { index: "02", title: "交给 Agent", description: "把选中的路径发给 Agent。MCP 由 Agent 以 stdio 启动。" },
  { index: "03", title: "开始使用", description: "技能安装到当前工作目录的 skills。MCP 在重启 Agent 后生效。" },
];

function currentPath() {
  const path = window.location.pathname.replace(/\/+$/, "");
  return path || "/";
}

export default function App() {
  const path = currentPath();
  const [copied, setCopied] = useState("");

  useEffect(() => {
    const titles: Record<string, string> = {
      "/": "food4agent · Agent 的技能和工具",
      "/skills": "food4agent · 技能",
      "/mcp": "food4agent · MCP",
    };
    document.title = titles[path] ?? "food4agent";
  }, [path]);

  async function copyText(key: string, value: string) {
    await navigator.clipboard.writeText(value);
    setCopied(key);
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <SiteHeader path={path} />
      <main>
        {path === "/" && <Home />}
        {path === "/skills" && <SkillCatalog copied={copied} onCopy={copyText} />}
        {path === "/mcp" && <McpCatalog copied={copied} onCopy={copyText} />}
        {path !== "/" && path !== "/skills" && path !== "/mcp" && <Missing />}
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
            <a key={link.href} href={link.href} className={path === link.href ? "bg-primary px-2 text-primary-foreground" : undefined}>
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
        badge="技能与 MCP"
        title="给 Agent 的技能和工具，"
        titleHighlight="直接选用。"
        description="网站收录的技能在 /skills，MCP 在 /mcp。用 GitHub 链接或本机 food4agent 仓库路径安装，不绑定某一个宿主。"
        primaryAction={{ label: "查看技能", href: "/skills" }}
        secondaryAction={{ label: "查看 MCP", href: "/mcp" }}
      />

      <section className="px-4 pb-8 md:px-8 lg:px-16">
        <div className="mx-auto grid max-w-6xl gap-6 md:grid-cols-2">
          <Card interactive>
            <a href="/skills" className="block">
              <CardHeader>
                <CardDescription>skills</CardDescription>
                <CardTitle>技能</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">收录 {skills.length} 个技能。每项都有 GitHub 路径和本机路径。</p>
              </CardContent>
            </a>
          </Card>
          <Card interactive>
            <a href="/mcp" className="block">
              <CardHeader>
                <CardDescription>mcp</CardDescription>
                <CardTitle>MCP</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">收录 {mcps.length} 个 MCP。由 Agent 以 stdio 启动 server.py。</p>
              </CardContent>
            </a>
          </Card>
        </div>
      </section>

      <section id="install" className="px-4 py-16 md:px-8 lg:px-16">
        <div className="mx-auto max-w-6xl">
          <div className="mb-10 space-y-3">
            <p className="text-sm font-bold uppercase tracking-widest text-primary">安装</p>
            <h2 className="text-3xl font-black uppercase tracking-tight md:text-5xl">两条路径，同一份内容。</h2>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {steps.map((step) => (
              <Card key={step.index}>
                <CardHeader>
                  <CardDescription>{step.index}</CardDescription>
                  <CardTitle>{step.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">{step.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
          <pre className="mt-6 overflow-x-auto whitespace-pre-wrap break-all border-3 border-foreground bg-muted p-4 text-sm">{`GitHub：${repoUrl}/skills/<name>
本机：skills/<name>`}</pre>
        </div>
      </section>

      <FAQAccordion
        subtitle="问题"
        title="常见问题"
        items={[
          { question: "food4agent 是什么？", answer: "给 Agent 提供 Skill 和 MCP 的仓库。技能目录在 /skills，MCP 目录在 /mcp。" },
          { question: "怎样安装 Skill？", answer: "打开 /skills，复制 GitHub 路径或本机路径发给 Agent。安装到当前工作目录的 skills/<name>。再次安装前先删除同名目录。" },
          { question: "MCP 怎么接入？", answer: "打开 /mcp，让 Agent 以 stdio 启动 python3 server.py，工作目录指向本机仓库里的 mcp/<name>，然后重启 Agent。" },
          { question: "目录名有什么要求？", answer: "只用小写字母、数字和短横线。目录名必须等于 SKILL.md 里的 name。" },
          { question: "仓库更新后怎么办？", answer: "GitHub 路径指向 main 的最新内容，重新安装即可。本机路径更新仓库后再安装。MCP 改完代码后重启 Agent。" },
        ]}
      />
      <FooterSimple
        logo="food4agent"
        links={[
          { label: "技能", href: "/skills" },
          { label: "MCP", href: "/mcp" },
          { label: "仓库", href: repoUrl },
        ]}
        copyright="food4agent · Skill 与 MCP"
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
          <h1 className="text-3xl font-black uppercase tracking-tight md:text-5xl">收录的技能</h1>
          <p className="max-w-3xl text-muted-foreground">把其中一条路径发给 Agent。安装到当前工作目录的同名目录。再次安装前先删除已有目录。</p>
        </div>
        <div className="grid gap-6">
          {skills.map((skill) => {
            const github = githubSkillUrl(skill.name);
            const local = localSkillPath(skill.name);
            return (
              <Card key={skill.name} id={skill.name}>
                <CardHeader>
                  <CardDescription>skills/{skill.name}</CardDescription>
                  <CardTitle className="normal-case">{skill.name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">{skill.summary}</p>
                  <pre className="overflow-x-auto whitespace-pre-wrap break-all border-3 border-foreground bg-muted p-4 text-sm">{github}</pre>
                  <pre className="overflow-x-auto whitespace-pre-wrap break-all border-3 border-foreground bg-muted p-4 text-sm">{local}</pre>
                  <div className="flex flex-wrap gap-3">
                    <CopyButton copied={copied === `${skill.name}:github`} label="复制 GitHub 路径" onClick={() => onCopy(`${skill.name}:github`, github)} />
                    <CopyButton copied={copied === `${skill.name}:local`} label="复制本机路径" onClick={() => onCopy(`${skill.name}:local`, local)} outline />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function McpCatalog({ copied, onCopy }: { copied: string; onCopy: (key: string, value: string) => void }) {
  return (
    <section className="px-4 py-16 md:px-8 lg:px-16">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 space-y-3">
          <p className="text-sm font-bold uppercase tracking-widest text-primary">/mcp</p>
          <h1 className="text-3xl font-black uppercase tracking-tight md:text-5xl">收录的 MCP</h1>
          <p className="max-w-3xl text-muted-foreground">由 Agent 以 stdio 启动 server.py。工作目录指向本机仓库里的 mcp 目录。仓库更新后重启 Agent。</p>
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
        <h1 className="text-3xl font-black uppercase tracking-tight">没有这个页面</h1>
        <p className="text-muted-foreground">技能在 /skills，MCP 在 /mcp。</p>
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
