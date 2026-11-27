import { useEffect, useLayoutEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { Search, X } from "lucide-react";
import { SkillCategoryNav, catalogHref } from "@/components/skill-category-nav";
import { SkillCopyButton } from "@/components/skill-copy-button";
import { SkillView } from "@/components/skill-view";
import { Button, buttonVariants } from "@/components/ui/button";
import { badgeVariants } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { SiteHeader } from "@/components/brand-logo";
import { categories } from "@/catalog";
import {
  createSkill,
  deleteSkill,
  fetchManifest,
  fetchSkill,
  fetchSkills,
  fetchToken,
  fetchVersions,
  loginAccount,
  logoutAccount,
  publishSkill,
  registerAccount,
  resetToken,
  rollbackSkill,
  saveDraft,
  updateSkill,
  uploadZip,
  type PublicManifest,
  type SkillChange,
  type SkillDetail,
  type SkillFile,
  type SkillSummary,
  type SkillVersion,
} from "@/console/api";
import type { ConsoleRoute } from "@/console/paths";
import { useSession } from "@/console/session";

export function ConsoleApp({ route }: { route: ConsoleRoute }) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <SiteHeader />
      <main className="px-4 py-8 md:px-8">
        <div className={`mx-auto w-full ${route.kind === "edit" ? "max-w-[1600px]" : "max-w-[1440px]"}`}>
          {route.kind === "login" && <LoginPage />}
          {route.kind === "profile" && <ProfilePage userId={route.userId} />}
          {route.kind === "token" && <TokenPage userId={route.userId} />}
          {route.kind === "list" && <SkillListPage userId={route.userId} />}
          {route.kind === "new" && <NewSkillPage userId={route.userId} />}
          {route.kind === "detail" && <SkillDetailPage userId={route.userId} name={route.name} token={route.token} />}
          {route.kind === "edit" && <SkillEditorPage userId={route.userId} name={route.name} />}
          {route.kind === "versions" && <VersionsPage userId={route.userId} name={route.name} />}
          {route.kind === "publish" && <PublishPage userId={route.userId} name={route.name} />}
        </div>
      </main>
    </div>
  );
}

function useOwner(userId: string) {
  const session = useSession();
  useEffect(() => {
    if (session.status === "guest") {
      window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
    }
  }, [session.status]);
  return session;
}

function Crumbs({ userId, items, className = "mb-1" }: { userId: string; items: { href?: string; label: string }[]; className?: string }) {
  return (
    <nav aria-label="路径" className={`${className} flex flex-wrap items-center gap-2 text-sm font-bold uppercase tracking-widest`}>
      {items.length > 0 ? <a className="underline underline-offset-4" href={`/${userId}`}>/{userId}</a> : <span>/{userId}</span>}
      {items.map((item, index) => {
        const current = index === items.length - 1;
        return (
          <span key={`${item.label}-${index}`} className="inline-flex items-center gap-2">
            <span aria-hidden="true">/</span>
            {current || !item.href ? <span>{item.label}</span> : <a href={item.href}>{item.label}</a>}
          </span>
        );
      })}
    </nav>
  );
}

function PageHead({ userId, items = [], title, actions }: { userId: string; items?: { href?: string; label: string }[]; title: string; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        <Crumbs userId={userId} items={items} />
        <h1 className="text-3xl font-black uppercase">{title}</h1>
      </div>
      {actions && <div className="flex flex-wrap gap-3">{actions}</div>}
    </div>
  );
}

function LoginPage() {
  const session = useSession();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [userId, setUserId] = useState("");
  const [nickname, setNickname] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const next = safeNext(new URLSearchParams(window.location.search).get("next"));

  useLayoutEffect(() => {
    if (session.status === "in" && session.account) {
      window.location.replace(next || `/${session.account.user_id}`);
    }
  }, [session, next]);

  if (session.status !== "guest") return null;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const account = mode === "login"
        ? await loginAccount(userId, password)
        : await registerAccount(userId, nickname, password);
      window.location.href = next || `/${account.user_id}`;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "登录失败");
      setSubmitting(false);
    }
  }

  return (
    <Card className="mx-auto max-w-md">
      <CardHeader>
        <CardTitle>{mode === "login" ? "登录" : "注册账号"}</CardTitle>
        <CardDescription>用户 ID 会写进主页地址，创建后不要改。昵称可以以后再改。</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={(event) => void submit(event)}>
          <Field label="用户 ID" value={userId} onChange={setUserId} autoComplete="username" />
          {mode === "register" && <Field label="昵称" value={nickname} onChange={setNickname} />}
          <Field label="密码" value={password} onChange={setPassword} type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} />
          {error && <ErrorText>{error}</ErrorText>}
          <Button type="submit" disabled={submitting} className="w-full">{submitting ? "提交中" : mode === "login" ? "登录" : "注册"}</Button>
        </form>
        <button className="mt-4 text-sm font-bold underline" type="button" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "没有账号，去注册" : "已有账号，去登录"}
        </button>
      </CardContent>
    </Card>
  );
}

function ProfilePage({ userId }: { userId: string }) {
  const session = useSession();
  if (session.status === "loading") return <p className="font-bold">加载中</p>;
  const owner = session.account?.user_id === userId;
  return (
    <PageHead
      userId={userId}
      title={owner ? session.account?.nickname || userId : userId}
      actions={(
        <>
          <a className={buttonVariants()} href={`/${userId}/skills`}>技能</a>
          {owner && <a className={buttonVariants({ variant: "outline" })} href={`/${userId}/token`}>令牌</a>}
          {owner && <Button variant="outline" onClick={() => void logoutAccount().then(() => { window.location.href = "/login"; })}>退出</Button>}
        </>
      )}
    />
  );
}

function TokenPage({ userId }: { userId: string }) {
  const session = useOwner(userId);
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (session.status !== "in" || session.account?.user_id !== userId) return;
    fetchToken().then((result) => setToken(result.token)).catch((caught) => setError(caught instanceof Error ? caught.message : "加载失败"));
  }, [session, userId]);

  if (session.status !== "in" || !session.account) return <p className="font-bold">加载中</p>;
  if (session.account.user_id !== userId) return <WrongAccount userId={session.account.user_id} />;

  async function reset() {
    setBusy(true);
    setError("");
    try {
      const result = await resetToken();
      setToken(result.token);
      setCopied(false);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "重置失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <PageHead
        userId={userId}
        items={[{ label: "令牌" }]}
        title="令牌"
        actions={(
          <>
            <Button variant="outline" disabled={!token} onClick={() => void copyText(token).then(() => setCopied(true))}>{copied ? "已复制" : "复制令牌"}</Button>
            <Button disabled={busy} onClick={() => void reset()}>{busy ? "重置中" : "重置令牌"}</Button>
          </>
        )}
      />
      <p className="text-sm text-muted-foreground">每个账号只有一个令牌，注册时自动生成，可以访问这个账号下的全部私有技能。重置后，旧令牌和带旧令牌的链接会失效。</p>
      {error && <ErrorText>{error}</ErrorText>}
      <p className="break-all border-3 border-foreground bg-background p-4 font-mono text-sm shadow-[4px_4px_0px_hsl(var(--shadow-color))]">{token || "加载中"}</p>
    </div>
  );
}

function SkillListPage({ userId }: { userId: string }) {
  const session = useOwner(userId);
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const params = new URLSearchParams(window.location.search);
  const requestedCategory = params.get("category");
  const query = (params.get("q") ?? "").trim();
  const terms = query.toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const pathname = `/${userId}/skills`;

  useEffect(() => {
    if (session.status !== "in" || session.account?.user_id !== userId) return;
    void Promise.all([fetchSkills(), fetchToken()])
      .then(([skillResult, tokenResult]) => {
        setSkills(skillResult.skills);
        setToken(tokenResult.token);
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "加载失败"));
  }, [session, userId]);

  if (session.status !== "in" || !session.account) return <p className="font-bold">加载中</p>;
  if (session.account.user_id !== userId) return <WrongAccount userId={session.account.user_id} />;

  const presetIDs = new Set(categories.map((item) => item.id));
  const counts = new Map<string, { label: string; count: number }>();
  for (const skill of skills) {
    if (!categoryLabel(skill.category_id, skill.category_label)) continue;
    const current = counts.get(skill.category_id) ?? { label: skill.category_label || skill.category_id, count: 0 };
    current.count += 1;
    counts.set(skill.category_id, current);
  }
  const categoryOptions = [
    { id: "", label: "全部", count: skills.length },
    ...categories.flatMap((item) => {
      const count = counts.get(item.id)?.count ?? 0;
      return count > 0 ? [{ id: item.id, label: item.label, count }] : [];
    }),
    ...[...counts.entries()].filter(([id]) => !presetIDs.has(id)).map(([id, item]) => ({ id, label: item.label, count: item.count })),
  ];
  const knownCategory = !requestedCategory || presetIDs.has(requestedCategory) || counts.has(requestedCategory);
  const filtered = knownCategory ? skills.filter((skill) => {
    if (requestedCategory && skill.category_id !== requestedCategory) return false;
    const text = `${skill.name} ${skill.display_name} ${skill.description}`.toLocaleLowerCase();
    return terms.every((term) => text.includes(term));
  }) : [];

  function installURL(skill: SkillSummary) {
    const page = `${window.location.origin}/${userId}/skills/${skill.name}`;
    return skill.visibility === "private" ? `${page}/g/${token}` : page;
  }

  async function copySkill(skill: SkillSummary, value: string) {
    if (skill.visibility === "private" && !token) {
      setError("令牌还没加载");
      return false;
    }
    await copyText(value);
  }

  return (
    <div className="space-y-6">
      <PageHead userId={userId} items={[{ label: "技能" }]} title="技能" actions={<a className={buttonVariants()} href={`/${userId}/skills/new`}>新建 Skill</a>} />
      {error && <ErrorText>{error}</ErrorText>}
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <SkillCategoryNav className="mb-0 min-w-0 flex-1" options={categoryOptions} pathname={pathname} selectedId={knownCategory ? requestedCategory ?? "" : null} query={query} />
        <form role="search" action={pathname} method="get" className="flex w-full shrink-0 gap-2 md:w-96">
          {requestedCategory !== null && <input type="hidden" name="category" value={requestedCategory} />}
          <input type="search" name="q" aria-label="搜索 Skill" placeholder="搜索名称或简介" defaultValue={query} className="h-11 min-w-0 flex-1 border-3 border-foreground bg-card px-3 text-sm shadow-[4px_4px_0px_hsl(var(--shadow-color))] outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" />
          <Button type="submit" size="icon" className="shrink-0" aria-label="搜索"><Search /></Button>
          {query && <Button variant="outline" size="icon" className="shrink-0" asChild><a href={catalogHref(pathname, 1, requestedCategory ?? "")} aria-label="清除搜索"><X /></a></Button>}
        </form>
      </div>
      {!knownCategory ? (
        <div className="space-y-4 border-3 border-foreground bg-muted p-6">
          <p>没有找到分类“{requestedCategory}”。</p>
          <Button asChild><a href={pathname}>返回全部技能</a></Button>
        </div>
      ) : filtered.length === 0 ? <p className="border-3 border-foreground bg-card p-6 shadow-[4px_4px_0px_hsl(var(--shadow-color))]">{skills.length === 0 ? "还没有 Skill。" : "没有找到匹配的技能。"}</p> : (
        <div className="grid gap-6">
          {filtered.map((skill) => (
            <Card key={skill.name}>
              <div className="flex flex-col gap-5 p-5 md:flex-row md:items-center md:justify-between md:p-6">
                <div className="min-w-0 space-y-3">
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                    <CardTitle className="min-w-0 normal-case leading-snug">
                      <a className="hover:underline" href={`/${userId}/skills/${skill.name}`}>{skill.display_name || skill.name}</a>
                    </CardTitle>
                    {categoryLabel(skill.category_id, skill.category_label) && <a href={catalogHref(pathname, 1, skill.category_id, query)} className={badgeVariants({ variant: "outline" })}>{categoryLabel(skill.category_id, skill.category_label)}</a>}
                    <Tag>{skill.visibility === "public" ? "公开" : "私有"}</Tag>
                    <Tag>{shortHash(skill.current_content_hash)}</Tag>
                    <Tag>{formatTime(skill.updated_at)}</Tag>
                    {skill.dirty && <Tag draft>草稿</Tag>}
                  </div>
                  <p className="line-clamp-2 text-sm leading-relaxed text-muted-foreground">{skill.description || skill.name}</p>
                </div>
                <div className="flex shrink-0 flex-wrap gap-3">
                  <SkillCopyButton size="sm" url={installURL(skill)} onCopy={(value) => copySkill(skill, value)} />
                  <a className={buttonVariants({ variant: "outline", size: "sm" })} href={`/${userId}/skills/${skill.name}/edit`}>编辑</a>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}


function NewSkillPage({ userId }: { userId: string }) {
  const session = useOwner(userId);
  const [name, setName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] = useState("private");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  if (session.status !== "in" || !session.account) return <p className="font-bold">加载中</p>;
  if (session.account.user_id !== userId) return <WrongAccount userId={session.account.user_id} />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const detail = await createSkill({ name, display_name: displayName, description, visibility });
      window.location.href = `/${userId}/skills/${detail.skill.name}/edit`;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "创建失败");
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      <PageHead userId={userId} items={[{ href: `/${userId}/skills`, label: "技能" }, { label: "新建" }]} title="新建 Skill" />
      <Card>
        <CardContent>
          <form className="space-y-4" onSubmit={(event) => void submit(event)}>
            <div className="grid grid-cols-[minmax(0,1fr)_11rem] items-end gap-x-4 gap-y-2">
              <span className="text-sm font-bold uppercase">Skill ID</span>
              <span className="text-sm font-bold uppercase">可见性</span>
              <Input value={name} placeholder="xxx-xxx（英文）" onChange={(event) => setName(event.target.value)} />
              <div className="relative">
                <Select value={visibility} onValueChange={setVisibility}>
                  <SelectTrigger className="focus:translate-x-0 focus:translate-y-0 focus:shadow-[4px_4px_0px_hsl(var(--shadow-color))]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="private">私有</SelectItem>
                    <SelectItem value="public">公开</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Field label="名称" value={displayName} onChange={setDisplayName} placeholder="填写技能名称" />
            <label className="block space-y-2 text-sm font-bold uppercase">
              <span>简介</span>
              <Textarea value={description} onChange={(event) => setDescription(event.target.value)} />
            </label>
            {error && <ErrorText>{error}</ErrorText>}
            <Button type="submit" disabled={submitting}>{submitting ? "创建中" : "创建"}</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function categoryLabel(id: string, label: string) {
  if (!id || !label || id === "未分类" || label === "未分类") return "";
  return label;
}

function accountInstallURL(userId: string, name: string, visibility: string, token: string) {
  const page = `${window.location.origin}/${userId}/skills/${name}`;
  return visibility === "private" ? `${page}/g/${token}` : page;
}

function SkillDetailPage({ userId, name, token }: { userId: string; name: string; token: string }) {
  const session = useSession();
  const [info, setInfo] = useState<SkillSummary | null>(null);
  const [manifest, setManifest] = useState<PublicManifest | null | undefined>(undefined);
  const [accessToken, setAccessToken] = useState(token);
  const [missing, setMissing] = useState(false);
  const owner = session.account?.user_id === userId;

  useEffect(() => {
    if (session.status === "loading") return;
    let cancelled = false;
    async function load() {
      try {
        if (owner || token) {
          const detail = await fetchSkill(name, owner ? "" : token);
          if (cancelled) return;
          setInfo(detail.skill);
          let pageToken = token;
          if (owner && detail.skill.visibility === "private") {
            pageToken = (await fetchToken()).token;
            if (!cancelled) setAccessToken(pageToken);
          }
          try {
            const published = await fetchManifest(userId, name, pageToken);
            if (!cancelled) setManifest(published);
          } catch {
            if (!cancelled) setManifest(null);
          }
          return;
        }
        const published = await fetchManifest(userId, name);
        if (cancelled) return;
        setManifest(published);
        setInfo({
          name: published.name,
          display_name: published.display_name || published.name,
          description: published.description || "",
          category_id: published.category_id || "",
          category_label: published.category_label || published.category_id || "",
          visibility: "public",
          current_content_hash: "",
          version: published.version,
          dirty: false,
          updated_at: "",
        });
      } catch {
        if (!cancelled) setMissing(true);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [session.status, owner, userId, name, token]);

  if (missing) return <MissingSkill />;
  if (!info || (manifest === undefined && !missing)) return <p className="font-bold">加载中</p>;
  const root = token ? `/${userId}/skills/${name}/g/${encodeURIComponent(token)}` : `/${userId}/skills/${name}`;
  const files = (manifest?.files ?? []).map((file) => ({ path: file.path, size: file.size, href: `${root}/${file.path}` }));
  const installURL = info.visibility === "private" && !accessToken ? "" : accountInstallURL(userId, name, info.visibility, accessToken);
  return (
    <SkillView
      leading={<Crumbs className="" userId={userId} items={[{ href: `/${userId}/skills`, label: "技能" }, { label: name }]} />}
      title={info.display_name || name}
      category={categoryLabel(info.category_id, info.category_label) ? { href: catalogHref(`/${userId}/skills`, 1, info.category_id), label: categoryLabel(info.category_id, info.category_label) } : undefined}
      description={info.description}
      actions={owner ? <a className={buttonVariants()} href={`/${userId}/skills/${name}/edit`}>编辑草稿</a> : undefined}
      installURL={installURL}
      version={manifest?.version || info.version}
      files={files}
      filesStatus={manifest ? "ready" : "missing"}
      manifestHref={manifest ? `${root}/manifest.json` : undefined}
    />
  );
}

function SkillEditorPage({ userId, name }: { userId: string; name: string }) {
  const session = useOwner(userId);
  const [detail, setDetail] = useState<SkillDetail | null>(null);
  const [files, setFiles] = useState<SkillFile[]>([]);
  const [selected, setSelected] = useState("SKILL.md");
  const [newPath, setNewPath] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [description, setDescription] = useState("");
  const [categoryID, setCategoryID] = useState("__none__");
  const [newCategory, setNewCategory] = useState("");
  const [visibility, setVisibility] = useState("private");
  const [knownCategories, setKnownCategories] = useState<{ id: string; label: string }[]>([]);
  const [confirmName, setConfirmName] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    if (session.status !== "in" || session.account?.user_id !== userId) return;
    fetchSkill(name).then((next) => {
      setDetail(next);
      setFiles(next.files);
      setSelected(next.files[0]?.path ?? "SKILL.md");
      setDisplayName(next.skill.display_name);
      setDescription(next.skill.description);
      setCategoryID(next.skill.category_id || "__none__");
      setVisibility(next.skill.visibility);
    }).catch((caught) => setError(caught instanceof Error ? caught.message : "加载失败"));
    fetchSkills().then((result) => {
      const map = new Map<string, string>();
      for (const skill of result.skills) {
        if (skill.category_id) map.set(skill.category_id, skill.category_label || skill.category_id);
      }
      setKnownCategories([...map].map(([id, label]) => ({ id, label })));
    }).catch(() => undefined);
  }, [session, userId, name]);

  if (session.status !== "in" || !session.account) return <p className="font-bold">加载中</p>;
  if (session.account.user_id !== userId) return <WrongAccount userId={session.account.user_id} />;
  const current = files.find((file) => file.path === selected);
  const categoryChoices = new Map<string, string>();
  for (const item of categories) categoryChoices.set(item.id, item.label);
  for (const item of knownCategories) categoryChoices.set(item.id, item.label);
  if (detail?.skill.category_id) categoryChoices.set(detail.skill.category_id, detail.skill.category_label || detail.skill.category_id);

  function updateContent(content: string) {
    setFiles((items) => items.map((file) => file.path === selected ? { ...file, content } : file));
  }

  async function save() {
    const category = categoryID === "__new__" ? newCategory.trim() : categoryID === "__none__" ? "未分类" : categoryID;
    if (categoryID === "__new__" && !category) {
      setError("请填写分类");
      return;
    }
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await updateSkill(name, { display_name: displayName, description, category, visibility });
      const next = await saveDraft(name, files);
      setDetail(next);
      setFiles(next.files);
      setDisplayName(next.skill.display_name);
      setDescription(next.skill.description);
      setCategoryID(next.skill.category_id || "__none__");
      setNewCategory("");
      setVisibility(next.skill.visibility);
      if (next.skill.category_id) {
        setKnownCategories((items) => items.some((item) => item.id === next.skill.category_id) ? items : [...items, { id: next.skill.category_id, label: next.skill.category_label }]);
      }
      setMessage("草稿已保存");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "保存失败");
    } finally {
      setBusy(false);
    }
  }

  async function removeSkill() {
    if (confirmName !== name) return;
    setBusy(true);
    setError("");
    try {
      await deleteSkill(name);
      window.location.href = `/${userId}/skills`;
    } catch (caught) {
      dialogRef.current?.close();
      setError(caught instanceof Error ? caught.message : "删除失败");
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <PageHead userId={userId} items={[{ href: `/${userId}/skills`, label: "技能" }, { href: `/${userId}/skills/${name}`, label: name }, { label: "编辑" }]} title={name} />
      {error && <ErrorText>{error}</ErrorText>}
      {message && <p className="font-bold">{message}</p>}
      <div className="grid gap-4 lg:grid-cols-[240px_minmax(0,1fr)_320px] lg:items-start">
        <section className="space-y-3 border-3 border-foreground bg-card p-4 shadow-[4px_4px_0px_hsl(var(--shadow-color))]">
          <h2 className="font-black uppercase">文件</h2>
          <div className="flex flex-col gap-2">
            {[...files].sort((a, b) => compareSkillPaths(a.path, b.path)).map((file) => (
              <button key={file.path} type="button" style={{ marginLeft: fileDepth(file.path) * 16 }} className={`break-all border-3 border-foreground px-3 py-2 text-left text-sm font-bold ${file.path === selected ? "bg-primary" : "bg-background"}`} onClick={() => setSelected(file.path)}>
                {file.path}
              </button>
            ))}
          </div>
          <Input value={newPath} placeholder="references/a.md" onChange={(event) => setNewPath(event.target.value)} />
          <Button type="button" className="w-full" onClick={() => {
            const path = newPath.trim();
            if (!path || files.some((file) => file.path === path)) return;
            setFiles((items) => [...items, { path, sha256: "", size: 0, content: "" }]);
            setSelected(path);
            setNewPath("");
          }}>添加文件</Button>
          <label className="block space-y-2 text-sm font-bold uppercase">
            <span>上传 ZIP</span>
            <Input type="file" accept=".zip,application/zip" onChange={(event) => {
              const file = event.target.files?.[0];
              if (!file) return;
              setBusy(true);
              void uploadZip(name, file).then((next) => {
                setDetail(next);
                setFiles(next.files);
                setSelected(next.files[0]?.path ?? "SKILL.md");
                setMessage("草稿已替换");
              }).catch((caught) => setError(caught instanceof Error ? caught.message : "上传失败")).finally(() => setBusy(false));
            }} />
          </label>
          <a className={buttonVariants({ variant: "secondary", className: "w-full" })} href={`/${userId}/skills/${name}/versions`}>历史版本</a>
        </section>

        <section className="min-w-0 space-y-3 border-3 border-foreground bg-card p-4 shadow-[4px_4px_0px_hsl(var(--shadow-color))]">
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-black uppercase">{selected || "未选择文件"}</h2>
            {current && <Button variant="destructive" size="sm" onClick={() => setFiles((items) => items.filter((file) => file.path !== selected))}>删除文件</Button>}
          </div>
          {!current && <p>选择一个文件。</p>}
          {current?.binary && <p>这是二进制文件，用 ZIP 替换。</p>}
          {current && !current.binary && <Textarea className="min-h-[70vh] font-mono" value={current.content ?? ""} onChange={(event) => updateContent(event.target.value)} />}
        </section>

        <aside className="space-y-4 border-3 border-foreground bg-card p-4 text-sm shadow-[4px_4px_0px_hsl(var(--shadow-color))]">
          <section className="space-y-3">
            <h2 className="font-black uppercase">技能信息</h2>
            <label className="block space-y-2 font-bold uppercase">
              <span>名称</span>
              <Input value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
            </label>
            <label className="block space-y-2 font-bold uppercase">
              <span>简介</span>
              <Textarea className="min-h-24" value={description} onChange={(event) => setDescription(event.target.value)} />
            </label>
            <label className="block space-y-2 font-bold uppercase">
              <span>分类</span>
              <Select value={categoryID} onValueChange={setCategoryID}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">未分类</SelectItem>
                  {[...categoryChoices].map(([id, label]) => <SelectItem key={id} value={id}>{label}</SelectItem>)}
                  <SelectItem value="__new__">新建分类</SelectItem>
                </SelectContent>
              </Select>
            </label>
            {categoryID === "__new__" && <Input value={newCategory} placeholder="分类名称" onChange={(event) => setNewCategory(event.target.value)} />}
            <label className="block space-y-2 font-bold uppercase">
              <span>可见性</span>
              <Select value={visibility} onValueChange={setVisibility}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="private">私有</SelectItem>
                  <SelectItem value="public">公开</SelectItem>
                </SelectContent>
              </Select>
            </label>
          </section>
          <section className="space-y-3 border-t-[3px] border-foreground pt-4">
            <Button className="w-full" variant="outline" disabled={busy} onClick={() => void save()}>保存草稿</Button>
            <a className={buttonVariants({ className: "w-full" })} href={`/${userId}/skills/${name}/releases/new`}>发布版本</a>
            <p className="text-muted-foreground">分类和可见性保存后立即生效，Skill 内容需要保存后发布版本后生效。当前版本{shortHash(detail?.skill.current_content_hash ?? "")}</p>
            <Button className="w-full" variant="destructive" disabled={busy} onClick={() => { setConfirmName(""); dialogRef.current?.showModal(); }}>删除</Button>
            <p className="text-muted-foreground">删除后，安装地址、草稿和全部版本都会失效，不能恢复。</p>
          </section>
        </aside>
      </div>
      <dialog ref={dialogRef} className="m-auto h-fit w-[min(28rem,calc(100%-2rem))] border-3 border-foreground bg-card p-6 text-foreground shadow-[8px_8px_0px_hsl(var(--shadow-color))] backdrop:bg-black/40">
        <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); void removeSkill(); }}>
          <h2 className="text-xl font-black">删除 {name}</h2>
          <p>输入完整技能标识后才能删除。</p>
          <Input value={confirmName} autoComplete="off" placeholder={name} onChange={(event) => setConfirmName(event.target.value)} />
          <div className="flex flex-wrap gap-3">
            <Button type="submit" variant="destructive" disabled={busy || confirmName !== name}>确认删除</Button>
            <Button type="button" variant="outline" onClick={() => dialogRef.current?.close()}>取消</Button>
          </div>
        </form>
      </dialog>
    </div>
  );
}

function VersionsPage({ userId, name }: { userId: string; name: string }) {
  const session = useOwner(userId);
  const [versions, setVersions] = useState<SkillVersion[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    if (session.status !== "in" || session.account?.user_id !== userId) return;
    fetchVersions(name).then((result) => setVersions(result.versions)).catch((caught) => setError(caught instanceof Error ? caught.message : "加载失败"));
  }, [session, userId, name]);
  if (session.status !== "in" || !session.account) return <p className="font-bold">加载中</p>;
  if (session.account.user_id !== userId) return <WrongAccount userId={session.account.user_id} />;
  return (
    <div className="space-y-4">
      <PageHead
        userId={userId}
        items={[{ href: `/${userId}/skills`, label: "技能" }, { href: `/${userId}/skills/${name}/edit`, label: name }, { label: "历史版本" }]}
        title="历史版本"
        actions={<a className={buttonVariants({ variant: "outline" })} href={`/${userId}`}>回到主页</a>}
      />
      {error && <ErrorText>{error}</ErrorText>}
      {versions.length === 0 && <p>还没有发布。</p>}
      {versions.map((version) => (
        <Card key={version.content_hash}>
          <div className="flex flex-col gap-5 p-5 md:flex-row md:items-center md:justify-between md:p-6">
            <div className="min-w-0 space-y-2">
              <CardTitle className="normal-case">{shortHash(version.content_hash)}</CardTitle>
              <p className="whitespace-pre-line text-sm text-muted-foreground">{formatTime(version.published_at)}{version.changelog ? `\n${version.changelog}` : ""}</p>
            </div>
            <Button className="shrink-0" variant="outline" onClick={() => void rollbackSkill(name, version.content_hash).then(() => { window.location.href = `/${userId}/skills/${name}`; }).catch((caught) => setError(caught instanceof Error ? caught.message : "回滚失败"))}>回滚到这个版本</Button>
          </div>
        </Card>
      ))}
      <p className="text-sm text-muted-foreground">只切换当前发布，不改这个版本里的文件。超过 10 个的旧版本会自动删除。</p>
    </div>
  );
}

function PublishPage({ userId, name }: { userId: string; name: string }) {
  const session = useOwner(userId);
  const [detail, setDetail] = useState<SkillDetail | null>(null);
  const [changelog, setChangelog] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const changelogFilled = useRef(false);
  useEffect(() => {
    if (session.status !== "in" || session.account?.user_id !== userId) return;
    let cancelled = false;
    fetchSkill(name).then((next) => {
      if (cancelled) return;
      setDetail(next);
      if (!changelogFilled.current) {
        changelogFilled.current = true;
        const notes = changeNotes(next.changes);
        if (notes) setChangelog(notes);
        else if (!next.skill.current_content_hash) setChangelog(`创建 ${next.skill.display_name || name} Skill`);
      }
    }).catch((caught) => {
      if (!cancelled) setError(caught instanceof Error ? caught.message : "加载失败");
    });
    return () => { cancelled = true; };
  }, [session, userId, name]);
  if (session.status !== "in" || !session.account) return <p className="font-bold">加载中</p>;
  if (session.account.user_id !== userId) return <WrongAccount userId={session.account.user_id} />;

  async function publish() {
    setBusy(true);
    setError("");
    try {
      if (detail) await saveDraft(name, detail.files);
      await publishSkill(name, changelog);
      window.location.href = `/${userId}/skills/${name}/versions`;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "发布失败");
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <PageHead
        userId={userId}
        items={[{ href: `/${userId}/skills`, label: "技能" }, { href: `/${userId}/skills/${name}/edit`, label: name }, { label: "发布" }]}
        title={`发布 ${name}`}
        actions={(
          <>
            <Button disabled={busy} onClick={() => void publish()}>{busy ? "发布中" : "发布"}</Button>
            <a className={buttonVariants({ variant: "outline" })} href={`/${userId}`}>回到主页</a>
          </>
        )}
      />
      <p className="text-sm text-muted-foreground">发布后生成不可变的内容哈希。私有技能用访问令牌下载。</p>
      <label className="block space-y-2 text-sm font-bold uppercase">
        <span>变更说明</span>
        <Textarea value={changelog} onChange={(event) => setChangelog(event.target.value)} />
      </label>
      {error && <ErrorText>{error}</ErrorText>}
    </div>
  );
}

function changeNotes(changes: SkillChange[]) {
  const label = { added: "新增", removed: "删除", modified: "修改" } as const;
  return changes.map((change) => `${label[change.status]} ${change.path}`).join("\n");
}

function WrongAccount({ userId }: { userId: string }) {
  return <p>当前登录的是 {userId}。<a className="font-bold underline" href={`/${userId}`}>回到自己的主页</a></p>;
}

function MissingSkill() {
  return (
    <Card>
      <CardHeader><CardTitle>找不到这个技能</CardTitle></CardHeader>
      <CardContent><a className={buttonVariants()} href="/skills">返回公共技能</a></CardContent>
    </Card>
  );
}

function Field({ label, value, onChange, type = "text", autoComplete, placeholder }: { label: string; value: string; onChange: (value: string) => void; type?: string; autoComplete?: string; placeholder?: string }) {
  return (
    <label className="block space-y-2 text-sm font-bold">
      <span className="uppercase">{label}</span>
      <Input value={value} type={type} autoComplete={autoComplete} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function ErrorText({ children }: { children: string }) {
  return <p className="border-3 border-foreground bg-destructive px-3 py-2 font-bold text-destructive-foreground">{children}</p>;
}

function Tag({ children, draft = false }: { children: string; draft?: boolean }) {
  return (
    <span className={draft
      ? "inline-flex items-center border-2 border-foreground bg-warning px-2 py-0.5 text-xs font-bold uppercase tracking-wide text-[#1a1a1a]"
      : "inline-flex items-center border-2 border-foreground bg-[#FFF6CC] px-2 py-0.5 text-xs font-bold uppercase tracking-wide text-[#1a1a1a]"}>
      {children}
    </span>
  );
}

function fileDepth(path: string) {
  return Math.max(0, path.split("/").filter(Boolean).length - 1);
}

function compareSkillPaths(a: string, b: string) {
  const left = a.split("/").filter(Boolean);
  const right = b.split("/").filter(Boolean);
  const count = Math.min(left.length, right.length);
  for (let i = 0; i < count; i++) {
    const leftFile = i === left.length - 1;
    const rightFile = i === right.length - 1;
    if (leftFile !== rightFile) return leftFile ? -1 : 1;
    const order = left[i].localeCompare(right[i], "zh", { numeric: true, sensitivity: "base" });
    if (order !== 0) return order;
  }
  return left.length - right.length;
}

async function copyText(value: string) {
  await navigator.clipboard.writeText(value);
}

function shortHash(value: string) {
  const bare = value.replace(/^sha256:/, "");
  return bare ? bare.slice(0, 6) : "未发布";
}

function formatTime(value: string) {
  if (!value) return "还没有";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "还没有";
  return date.toLocaleString("zh-CN", { hour12: false });
}

function safeNext(value: string | null) {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return "";
  return value;
}
