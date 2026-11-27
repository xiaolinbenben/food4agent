import type { ReactNode } from "react";
import { SkillCopyButton } from "@/components/skill-copy-button";
import { badgeVariants } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export type SkillFileLink = { path: string; size: number; href: string };

function fileDepth(path: string) {
  return Math.max(0, path.split("/").filter(Boolean).length - 1);
}

function shortVersion(value: string) {
  const bare = value.replace(/^sha256:/, "");
  return bare ? bare.slice(0, 6) : "未发布";
}

export function SkillView({
  leading,
  title,
  category,
  description,
  actions,
  installURL,
  version,
  files,
  filesStatus,
  manifestHref,
  emptyLabel = "还没有发布。",
}: {
  leading?: ReactNode;
  title: string;
  category?: { href: string; label: string };
  description?: string;
  actions?: ReactNode;
  installURL: string;
  version: string;
  files: SkillFileLink[];
  filesStatus: "loading" | "ready" | "missing";
  manifestHref?: string;
  emptyLabel?: string;
}) {
  return (
    <div className="space-y-8 [overflow-wrap:anywhere]">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex min-w-0 flex-col gap-3">
          {leading}
          <h1 className="text-3xl font-black leading-none tracking-tight md:text-5xl">{title}</h1>
          {category && <a href={category.href} className={`${badgeVariants({ variant: "outline" })} w-fit`}>{category.label}</a>}
          {description ? <p className="max-w-3xl text-muted-foreground">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </div>
      <Card>
        <CardHeader>
          <CardDescription>npx skills add</CardDescription>
          <CardTitle className="normal-case">安装命令</CardTitle>
        </CardHeader>
        <CardContent>
          {installURL ? (
            <div className="flex items-center gap-3">
              <pre className="min-w-0 flex-1 overflow-x-auto whitespace-pre-wrap break-all border-3 border-foreground bg-muted p-4 text-sm">{`npx skills add ${installURL}`}</pre>
              <SkillCopyButton url={installURL} />
            </div>
          ) : <p className="font-bold">加载中</p>}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center gap-2">
            <CardTitle className="normal-case">文件</CardTitle>
            <span className="inline-flex items-center border-2 border-foreground bg-[#FFF6CC] px-2 py-0.5 text-xs font-bold uppercase tracking-wide">{shortVersion(version)}</span>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {filesStatus === "loading" && <p className="font-bold">加载中</p>}
          {filesStatus === "missing" && <p>{emptyLabel}</p>}
          {filesStatus === "ready" && files.map((file) => (
            <p key={file.path} className="font-mono text-sm" style={{ paddingLeft: `${fileDepth(file.path) * 16}px` }}>
              <a className="underline" href={file.href}>{file.path}</a> · {file.size} 字节
            </p>
          ))}
          {filesStatus === "ready" && manifestHref && <p className="break-all text-sm"><a className="underline" href={manifestHref}>manifest.json</a></p>}
        </CardContent>
      </Card>
    </div>
  );
}
