import { useCallback, useEffect, useState } from "react";
import { Blocks, Check, Copy, FolderTree, PlugZap, RefreshCw, ScrollText, TerminalSquare } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CTASimple } from "@/components/blocks/cta-section";
import { FAQAccordion } from "@/components/blocks/faq-section";
import { FeatureGridWithIcons } from "@/components/blocks/feature-grid";
import { FooterSimple } from "@/components/blocks/footer-section";
import { HeroCentered } from "@/components/blocks/hero-section";
import { PricingSection } from "@/components/blocks/pricing-section";
import { fetchHealth, fetchWoodfish, knockWoodfish } from "@/lib/api";

const repoUrl = "https://github.com/xiaolinbenben/food4agent";
const githubSkillUrl = "https://github.com/xiaolinbenben/food4agent/skills/hello-world";
const localSkillPath = "skills/hello-world";
const mcpConfig = `command: python3
args: server.py
cwd: /你的路径/food4agent/mcp/hello-world`;

const steps = [
  { index: "01", title: "选一条路径", description: "GitHub 链接，或本机 food4agent 仓库里的 skills。两条路径是同一份技能。" },
  { index: "02", title: "交给 Agent", description: "把选中的路径发给 Agent。MCP 由 Agent 以 stdio 启动。" },
  { index: "03", title: "开始使用", description: "技能安装到当前工作目录的 skills。MCP 在重启 Agent 后生效。" },
];

export default function App() {
  const [copied, setCopied] = useState("");
  const [health, setHealth] = useState<"loading" | "online" | "offline">("loading");
  const [count, setCount] = useState<number | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setHealth("loading");
    try {
      const result = await fetchHealth();
      setHealth(result.data.status === "ok" ? "online" : "offline");
    } catch {
      setHealth("offline");
    }
    try {
      const woodfish = await fetchWoodfish();
      setCount(woodfish.data.count);
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "木鱼次数暂时读不到");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function copyText(key: string, value: string) {
    await navigator.clipboard.writeText(value);
    setCopied(key);
  }

  async function knock() {
    setPending(true);
    try {
      const result = await knockWoodfish();
      setCount(result.data.count);
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "没敲上");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b-3 border-foreground bg-background">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 md:px-8">
          <a href="#top" className="text-lg font-black uppercase tracking-tight">
            food4agent
          </a>
          <nav className="hidden items-center gap-5 text-sm font-bold uppercase md:flex">
            <a href="#install">接入</a>
            <a href="#steps">步骤</a>
            <a href="#capabilities">能力</a>
            <a href="#plans">方式</a>
            <a href="#faq">问题</a>
          </nav>
          <Button size="sm" variant="outline" asChild>
            <a href="/admin/">管理端</a>
          </Button>
        </div>
      </header>

      <main id="top">
        <HeroCentered
          badge="GitHub 或本机仓库 · MCP 以 stdio 启动"
          title="给 Agent 的技能和工具，"
          titleHighlight="开箱即用。"
          description="面向 Agent，不绑定某一个宿主。技能用 GitHub 链接或本机 food4agent 仓库路径安装，MCP 按 stdio 启动。"
          primaryAction={{ label: "查看接入方式", href: "#install" }}
          secondaryAction={{ label: "打开仓库", href: repoUrl }}
        />

        <section id="install" className="px-4 py-16 md:px-8 lg:px-16">
          <div className="mx-auto max-w-6xl">
            <div className="mb-10 space-y-3 text-center">
              <p className="text-sm font-bold uppercase tracking-widest text-primary">接入</p>
              <h2 className="text-3xl font-black uppercase tracking-tight md:text-5xl">选好入口，复制即可。</h2>
              <p className="text-muted-foreground">Skill 有两条路径，装的是同一份技能。要给 Agent 一个工具，用 MCP。</p>
            </div>
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardDescription>Skill</CardDescription>
                  <CardTitle>把路径发给 Agent</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground">GitHub 路径和本机 food4agent 路径都可以。安装到当前工作目录的同名 skills。安装前先删掉已有目录。</p>
                  <pre className="overflow-x-auto whitespace-pre-wrap break-all border-3 border-foreground bg-muted p-4 text-sm">{githubSkillUrl}</pre>
                  <pre className="overflow-x-auto whitespace-pre-wrap break-all border-3 border-foreground bg-muted p-4 text-sm">{localSkillPath}</pre>
                  <div className="flex flex-wrap gap-3">
                    <Button onClick={() => void copyText("github", githubSkillUrl)}>
                      {copied === "github" ? <Check /> : <Copy />}
                      {copied === "github" ? "已复制" : "复制 GitHub 路径"}
                    </Button>
                    <Button variant="outline" onClick={() => void copyText("local", localSkillPath)}>
                      {copied === "local" ? <Check /> : <Copy />}
                      {copied === "local" ? "已复制" : "复制 food4agent 路径"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-foreground text-background">
                <CardHeader className="border-background">
                  <CardDescription className="text-background/70">MCP</CardDescription>
                  <CardTitle className="text-background">以 stdio 启动</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-background/70">cwd 指向 mcp/hello-world。仓库更新后重启 Agent。</p>
                  <pre className="overflow-x-auto whitespace-pre-wrap break-all border-3 border-background bg-background p-4 text-sm text-foreground">{mcpConfig}</pre>
                  <Button variant="secondary" onClick={() => void copyText("mcp", mcpConfig)}>
                    {copied === "mcp" ? <Check /> : <Copy />}
                    {copied === "mcp" ? "已复制" : "复制 MCP 配置"}
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        <section className="px-4 md:px-8 lg:px-16">
          <div className="mx-auto max-w-6xl border-3 border-foreground bg-accent p-8 shadow-[8px_8px_0px_hsl(var(--shadow-color))] md:p-12">
            <h2 className="text-3xl font-black uppercase tracking-tight md:text-5xl">技能、工具和说明，一个仓库就够了。</h2>
            <p className="mt-4 max-w-3xl text-lg font-medium">它不是另一个聊天窗口，而是 Agent 进入可复用工作流的统一入口。原来要到处找脚本、改配置、复制目录的事，现在都从这里开始。</p>
          </div>
        </section>

        <section id="steps" className="px-4 py-16 md:px-8 lg:px-16">
          <div className="mx-auto max-w-6xl">
            <div className="mb-10 space-y-3">
              <p className="text-sm font-bold uppercase tracking-widest text-primary">三步</p>
              <h2 className="text-3xl font-black uppercase tracking-tight md:text-5xl">第一次使用，也只要三步。</h2>
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
          </div>
        </section>

        <div id="capabilities">
          <FeatureGridWithIcons
            subtitle="能力"
            title="开箱即用，不等于只有一句 hello。"
            description="现在仓库里是 hello-world。后面的技能和 MCP 也按同一套目录放进来。"
            columns={4}
            features={[
              { icon: <ScrollText />, title: "技能自带说明", description: "每个 Skill 有自己的 SKILL.md，脚本放在该技能目录里，随技能一起安装。" },
              { icon: <PlugZap />, title: "MCP 一个进程", description: "server.py 由 Agent 以 stdio 拉起，不另开服务。" },
              { icon: <FolderTree />, title: "目录即名称", description: "只用小写字母、数字和短横线。目录名等于链接最后一段，也等于技能名。" },
              { icon: <Blocks />, title: "两条路径同一份技能", description: "GitHub 路径指向 main 的最新内容。本机路径用你拿到的那份仓库。再次安装前先删除同名目录。" },
            ]}
          />
        </div>

        <section id="catalog" className="px-4 py-8 md:px-8 lg:px-16">
          <div className="mx-auto grid max-w-6xl gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardDescription>skills/hello-world</CardDescription>
                <CardTitle>示例技能</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <p>运行 scripts/hello.py，输出 hello world。</p>
                <a className="inline-flex font-bold uppercase text-foreground" href={githubSkillUrl}>
                  打开 Skill 目录
                </a>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardDescription>mcp/hello-world</CardDescription>
                <CardTitle>示例工具</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <p>提供 hello_world 工具，返回 hello world。</p>
                <a className="inline-flex font-bold uppercase text-foreground" href="https://github.com/xiaolinbenben/food4agent/mcp/hello-world">
                  打开 MCP 目录
                </a>
              </CardContent>
            </Card>
          </div>
        </section>

        <div id="plans">
          <PricingSection
            title="按需要选择接入方式。"
            subtitle="三种方式使用同一套仓库，只是 Agent 拿到的入口不同。没有套餐，也不用付费。"
            tiers={[
              {
                name: "Skill",
                price: "免费",
                period: "开源",
                description: "只要说明和脚本",
                features: ["GitHub 或本机仓库路径", "安装到当前工作目录的 skills", "适合文档和本地脚本"],
                cta: "复制 Skill 链接",
                ctaHref: "#install",
              },
              {
                name: "MCP",
                price: "免费",
                period: "开源",
                description: "只要一个工具",
                features: ["stdio 启动 server.py", "cwd 指向工具目录", "重启 Agent 后生效"],
                cta: "复制 MCP 配置",
                ctaHref: "#install",
              },
              {
                name: "一起用",
                price: "免费",
                period: "开源",
                description: "技能和工具都要",
                features: ["Skill 负责说明和脚本", "MCP 负责工具调用", "后续内容继续加在这个仓库"],
                cta: "查看两个入口",
                ctaHref: "#install",
                featured: true,
              },
            ]}
          />
        </div>

        <section id="console" className="px-4 py-8 md:px-8 lg:px-16">
          <div className="mx-auto grid max-w-6xl gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardDescription>管理端</CardDescription>
                <CardTitle>账号写在这里</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <dl className="space-y-3 text-sm">
                  <div className="flex items-center justify-between border-b-3 border-foreground pb-3">
                    <dt>账号</dt>
                    <dd className="font-mono font-bold">admin</dd>
                  </div>
                  <div className="flex items-center justify-between">
                    <dt>密码</dt>
                    <dd className="font-mono font-bold">admin123</dd>
                  </div>
                </dl>
                <Button variant="outline" asChild>
                  <a href="/admin/">打开管理端</a>
                </Button>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardDescription>示例接口</CardDescription>
                <CardTitle className="flex items-center gap-3">
                  <TerminalSquare />
                  木鱼 {count === null ? "—" : count}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">次数存在 SQLite 里，刷新还在。管理端读的是同一条记录。</p>
                <div className="flex flex-wrap items-center gap-3">
                  <Badge variant={health === "online" ? "success" : "warning"}>{health === "loading" ? "检查中" : health === "online" ? "服务正常" : "服务未启动"}</Badge>
                  <Button onClick={() => void knock()} disabled={pending}>
                    {pending ? "记下这一下…" : "敲一下"}
                  </Button>
                  <Button variant="outline" onClick={() => void refresh()} disabled={health === "loading"}>
                    <RefreshCw className={health === "loading" ? "animate-spin" : ""} />
                    刷新
                  </Button>
                </div>
                {error && <p className="text-sm font-bold text-destructive">{error}</p>}
              </CardContent>
            </Card>
          </div>
        </section>

        <div id="faq">
          <FAQAccordion
            subtitle="问题"
            title="常见问题"
            description="没有写到的，直接看仓库里的 README。"
            items={[
              { question: "food4agent 是什么？", answer: "给 Agent 提供 Skill 和 MCP 的仓库。Skill 是说明加脚本，MCP 是一个 stdio 工具进程。" },
              { question: "必须有 API Key 才能用吗？", answer: "安装本身不用。某个技能若要调用外部接口，按其说明提供 key。" },
              { question: "怎样安装 Skill？", answer: "GitHub 路径是 https://github.com/xiaolinbenben/food4agent/skills/hello-world。food4agent 路径是本机仓库里的 skills/hello-world。都安装到当前工作目录的 skills/hello-world。再次安装前先删除同名目录。" },
              { question: "MCP 怎么接入？", answer: "让 Agent 以 stdio 启动 python3 server.py，工作目录改成你机器上的 mcp/hello-world，然后重启 Agent。" },
              { question: "目录名有什么要求？", answer: "只用小写字母、数字和短横线。目录名必须等于 SKILL.md 里的 name。" },
              { question: "仓库更新后怎么办？", answer: "GitHub 路径指向 main 的最新内容，重新安装即可。本机路径更新仓库后再安装。MCP 改完代码后重启 Agent。" },
              { question: "管理端账号可以改吗？", answer: "不可以。参观账号固定是 admin / admin123，写在这个页面上。" },
              { question: "这是 OpenAI 官方产品吗？", answer: "不是。这是独立维护的 Skill 和 MCP 仓库，以及配套的全栈站点。和 OpenAI 没有隶属、授权或背书关系。" },
            ]}
          />
        </div>

        <CTASimple
          title="把路径发给 Agent，让它自己装上。"
          description="从一个 hello world 开始。后面的技能和工具继续放进 skills 和 mcp。"
          primaryAction={{ label: "复制 Skill 链接", href: "#install" }}
          secondaryAction={{ label: "查看 GitHub", href: repoUrl }}
        />
        <FooterSimple
          logo="food4agent"
          links={[
            { label: "仓库", href: repoUrl },
            { label: "Skill", href: githubSkillUrl },
            { label: "MCP", href: "https://github.com/xiaolinbenben/food4agent/mcp/hello-world" },
            { label: "管理端", href: "/admin/" },
          ]}
          copyright="food4agent · Skill 与 MCP"
        />
      </main>
    </div>
  );
}
