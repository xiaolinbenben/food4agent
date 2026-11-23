import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { Check, ChevronDown, Copy, Search, X } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { badgeVariants } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FAQAccordion } from "@/components/blocks/faq-section";
import { FooterSimple } from "@/components/blocks/footer-section";
import { HeroCentered } from "@/components/blocks/hero-section";
import { categories, githubMcpUrl, mcps, repoUrl, siteOrigin, siteSkillUrl, skills, type SkillEntry } from "@/catalog";

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

const catalogPageSize = 20;

function requestedPage() {
  const raw = new URLSearchParams(window.location.search).get("page");
  if (!raw || !/^[1-9]\d*$/.test(raw)) return 1;
  const page = Number(raw);
  return Number.isSafeInteger(page) ? page : 1;
}

function catalogHref(pathname: string, page: number, categoryId = "", query = "") {
  const params = new URLSearchParams();
  if (categoryId) params.set("category", categoryId);
  if (query) params.set("q", query);
  if (page > 1) params.set("page", String(page));
  const search = params.toString();
  return search ? `${pathname}?${search}` : pathname;
}

function pageSlice<T>(items: readonly T[], requested: number) {
  const total = items.length;
  const pageCount = Math.max(1, Math.ceil(total / catalogPageSize));
  const page = Math.min(requested, pageCount);
  const start = (page - 1) * catalogPageSize;
  return { items: items.slice(start, start + catalogPageSize), page, pageCount, start, total };
}

function rangeLabel(total: number, start: number, count: number) {
  if (total === 0 || count === total) return `共 ${total} 个。`;
  return `共 ${total} 个，本页 ${start + 1}-${start + count}。`;
}

function CatalogPager({ pathname, page, pageCount, categoryId, query, className }: { pathname: string; page: number; pageCount: number; categoryId?: string; query?: string; className?: string }) {
  if (pageCount <= 1) return null;
  return (
    <nav aria-label="分页" className={`flex flex-wrap items-center justify-between gap-3 ${className ?? ""}`}>
      <p className="text-sm font-bold">
        {page} / {pageCount}
      </p>
      <div className="flex flex-wrap gap-3">
        {page > 1 ? (
          <Button variant="outline" asChild>
            <a href={catalogHref(pathname, page - 1, categoryId, query)}>上一页</a>
          </Button>
        ) : (
          <Button variant="outline" disabled>
            上一页
          </Button>
        )}
        {page < pageCount ? (
          <Button asChild>
            <a href={catalogHref(pathname, page + 1, categoryId, query)}>下一页</a>
          </Button>
        ) : (
          <Button disabled>下一页</Button>
        )}
      </div>
    </nav>
  );
}

const categoryOptions = [
  { id: "", label: "全部", count: skills.length },
  ...categories.map((category) => ({ ...category, count: skills.filter((skill) => skill.categoryId === category.id).length })),
];

function SkillCategoryNav({ selectedId, query }: { selectedId: string | null; query: string }) {
  const containerRef = useRef<HTMLElement>(null);
  const measureRef = useRef<HTMLDivElement>(null);
  const [visibleCount, setVisibleCount] = useState(0);
  const [expandedCount, setExpandedCount] = useState(0);

  useLayoutEffect(() => {
    const container = containerRef.current!;
    const row = measureRef.current!;
    const measure = () => {
      const widths = Array.from(row.children, (element) => element.getBoundingClientRect().width);
      const moreWidth = widths.pop()!;
      const gap = parseFloat(getComputedStyle(row).columnGap);
      const available = container.clientWidth - 4;
      if (widths.reduce((sum, width) => sum + width, 0) + gap * (widths.length - 1) <= available) {
        setVisibleCount(widths.length);
        return;
      }
      let used = moreWidth;
      let count = 0;
      for (const width of widths) {
        if (used + gap + width > available) break;
        used += gap + width;
        count += 1;
      }
      setVisibleCount(count);
    };
    const observer = new ResizeObserver(measure);
    observer.observe(container);
    observer.observe(row);
    measure();
    return () => observer.disconnect();
  }, []);

  const shownCount = Math.min(visibleCount + expandedCount, categoryOptions.length);
  return (
    <nav ref={containerRef} aria-label="技能分类" className="relative mb-6 flex flex-wrap items-center gap-3">
      <div aria-hidden="true" className="pointer-events-none invisible absolute inset-0 overflow-hidden">
        <div ref={measureRef} className="flex w-max gap-3">
          {categoryOptions.map((item) => (
            <span key={item.id} className={buttonVariants({ variant: "outline", size: "sm" })}>
              {item.label}<span className="tabular-nums opacity-70">{item.count}</span>
            </span>
          ))}
          <span className={buttonVariants({ variant: "outline", size: "sm" })}>更多<ChevronDown /></span>
        </div>
      </div>
      {categoryOptions.slice(0, shownCount).map((item) => (
        <Button key={item.id} size="sm" variant={selectedId === item.id ? "default" : "outline"} className="shrink-0" asChild>
          <a href={catalogHref("/skills", 1, item.id, query)} aria-current={selectedId === item.id ? "page" : undefined}>
            {item.label}<span className="tabular-nums opacity-70">{item.count}</span>
          </a>
        </Button>
      ))}
      {shownCount < categoryOptions.length && (
        <Button size="sm" variant={categoryOptions.slice(shownCount).some((item) => item.id === selectedId) ? "default" : "outline"} className="shrink-0" onClick={() => setExpandedCount((count) => count + 10)}>
          更多<ChevronDown />
        </Button>
      )}
    </nav>
  );
}

function SkillCatalog({ copied, onCopy }: { copied: string; onCopy: (key: string, value: string) => void }) {
  const params = new URLSearchParams(window.location.search);
  const requestedCategory = params.get("category");
  const query = (params.get("q") ?? "").trim();
  const terms = query.toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const category = categories.find((item) => item.id === requestedCategory);
  const invalidCategory = requestedCategory !== null && !category;
  const filtered = (invalidCategory ? [] : category ? skills.filter((skill) => skill.categoryId === category.id) : skills).filter((skill) => {
    const text = `${skill.name} ${skill.summary}`.toLocaleLowerCase();
    return terms.every((term) => text.includes(term));
  });
  const slice = pageSlice(filtered, requestedPage());
  return (
    <section className="px-4 pt-6 pb-10 [overflow-wrap:anywhere] md:px-8 md:pt-8 lg:px-16">
      <div className="mx-auto max-w-6xl">
        <div className="mb-5 space-y-2">
          <p className="text-sm font-bold uppercase tracking-widest text-primary">/skills</p>
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between md:gap-8">
            <h1 className="min-w-0 text-3xl font-black tracking-tight md:text-5xl">{invalidCategory ? "分类不存在" : category?.label ?? "全部技能"}</h1>
            <form role="search" action="/skills" method="get" className="flex w-full shrink-0 gap-2 md:w-96">
              {requestedCategory !== null && <input type="hidden" name="category" value={requestedCategory} />}
              <input type="search" name="q" aria-label="搜索 Skill" placeholder="搜索名称或简介" defaultValue={query} className="h-11 min-w-0 flex-1 border-3 border-foreground bg-card px-3 text-sm shadow-[4px_4px_0px_hsl(var(--shadow-color))] outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" />
              <Button type="submit" size="icon" className="shrink-0" aria-label="搜索"><Search /></Button>
              {query && <Button variant="outline" size="icon" className="shrink-0" asChild><a href={catalogHref("/skills", 1, requestedCategory ?? "")} aria-label="清除搜索"><X /></a></Button>}
            </form>
          </div>
          <p className="max-w-3xl text-muted-foreground">复制地址发给 Agent。技能会装到当前项目里的同名目录。这个目录已经存在时，先删掉再装。</p>
        </div>
        <SkillCategoryNav selectedId={invalidCategory ? null : category?.id ?? ""} query={query} />
        {invalidCategory ? (
          <div className="space-y-4 border-3 border-foreground bg-muted p-6">
            <p>没有找到分类“{requestedCategory}”。请选择上方分类，或返回全部技能。</p>
            <Button asChild><a href="/skills">返回全部技能</a></Button>
          </div>
        ) : slice.total === 0 ? (
          <div className="border-3 border-foreground bg-muted p-6">
            <p>没有找到匹配的技能，请更换关键词或分类。</p>
          </div>
        ) : null}
        <div className="grid gap-4">
          {slice.items.map((skill) => (
            <SkillCard key={skill.name} skill={skill} query={query} copied={copied} onCopy={onCopy} />
          ))}
        </div>
        {!invalidCategory && (
          <div className="mt-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <p className="text-sm font-bold">{rangeLabel(slice.total, slice.start, slice.items.length)}</p>
            <CatalogPager pathname="/skills" page={slice.page} pageCount={slice.pageCount} categoryId={category?.id} query={query} className="gap-4" />
          </div>
        )}
      </div>
    </section>
  );
}

function skillInstallPrompt(url: string) {
  return `帮我安装 ${url} 这个技能`;
}

function SkillCategoryLink({ categoryId, query = "" }: { categoryId: string; query?: string }) {
  const category = categories.find((item) => item.id === categoryId)!;
  return (
    <a href={catalogHref("/skills", 1, category.id, query)} className={badgeVariants({ variant: "outline" })}>
      {category.label}
    </a>
  );
}

function SkillPage({ skill, copied, onCopy }: { skill: SkillEntry; copied: string; onCopy: (key: string, value: string) => void }) {
  const url = siteSkillUrl(skill.name);
  const prompt = skillInstallPrompt(url);
  return (
    <section className="px-4 py-16 [overflow-wrap:anywhere] md:px-8 lg:px-16">
      <div className="mx-auto max-w-6xl space-y-8">
        <div className="space-y-3">
          <p className="text-sm font-bold uppercase tracking-widest text-primary">
            <a href="/skills">全部技能</a>
          </p>
          <h1 className="text-3xl font-black tracking-tight md:text-5xl">{skill.name}</h1>
          <SkillCategoryLink categoryId={skill.categoryId} />
          <p className="max-w-3xl text-muted-foreground">{skill.summary}</p>
        </div>
        <Card>
          <CardHeader>
            <CardDescription>安装地址</CardDescription>
            <CardTitle className="normal-case">发给 Agent</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <pre className="overflow-x-auto whitespace-pre-wrap break-all border-3 border-foreground bg-muted p-4 text-sm">{url}</pre>
            <div className="flex flex-wrap gap-3">
              <CopyButton copied={copied === skill.name} label="复制地址" onClick={() => onCopy(skill.name, url)} />
              <CopyButton outline copied={copied === `${skill.name}:prompt`} label="复制安装口令" onClick={() => onCopy(`${skill.name}:prompt`, prompt)} />
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

function SkillCard({ skill, query, copied, onCopy }: { skill: SkillEntry; query: string; copied: string; onCopy: (key: string, value: string) => void }) {
  const url = siteSkillUrl(skill.name);
  const prompt = skillInstallPrompt(url);
  return (
    <Card id={skill.name}>
      <div className="flex flex-col gap-5 p-5 md:flex-row md:items-center md:justify-between md:p-6">
        <div className="min-w-0 space-y-3">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <CardTitle className="min-w-0 normal-case leading-snug">
              <a href={`/skills/${skill.name}`} className="hover:underline">{skill.name}</a>
            </CardTitle>
            <SkillCategoryLink categoryId={skill.categoryId} query={query} />
          </div>
          <p className="line-clamp-2 text-sm leading-relaxed text-muted-foreground">{skill.summary}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-3">
          <CopyButton size="sm" outline copied={copied === skill.name} label="复制地址" onClick={() => onCopy(skill.name, url)} />
          <CopyButton size="sm" copied={copied === `${skill.name}:prompt`} label="复制安装口令" onClick={() => onCopy(`${skill.name}:prompt`, prompt)} />
        </div>
      </div>
    </Card>
  );
}

function McpCatalog({ copied, onCopy }: { copied: string; onCopy: (key: string, value: string) => void }) {
  const slice = pageSlice(mcps, requestedPage());
  return (
    <section className="px-4 py-16 md:px-8 lg:px-16">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10 space-y-3">
          <p className="text-sm font-bold uppercase tracking-widest text-primary">/mcp</p>
          <h1 className="text-3xl font-black tracking-tight md:text-5xl">全部 MCP</h1>
          <p className="max-w-3xl text-muted-foreground">让 Agent 按下面的命令启动。cwd 换成你电脑上这份仓库里的对应目录。代码更新后，重新启动 Agent。</p>
          <p className="text-sm font-bold">{rangeLabel(slice.total, slice.start, slice.items.length)}</p>
          <CatalogPager pathname="/mcp" page={slice.page} pageCount={slice.pageCount} />
        </div>
        <div className="grid gap-6">
          {slice.items.map((mcp) => (
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
        <CatalogPager pathname="/mcp" page={slice.page} pageCount={slice.pageCount} className="mt-8" />
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

function CopyButton({ copied, label, onClick, outline, size }: { copied: boolean; label: string; onClick: () => void; outline?: boolean; size?: "sm" }) {
  return (
    <Button size={size} variant={outline ? "outline" : "default"} onClick={() => void onClick()}>
      {copied ? <Check /> : <Copy />}
      {copied ? "已复制" : label}
    </Button>
  );
}
