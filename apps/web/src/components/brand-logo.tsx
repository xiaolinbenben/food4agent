import type { ReactNode } from "react";
import { accountHomeHref, followAccountHome, useSession } from "@/console/session";
import { cn } from "@/lib/utils";

export function BrandLogo({ className }: { className?: string }) {
  return (
    <a href="/" className={cn("inline-flex items-center gap-2 text-lg font-black uppercase tracking-tight", className)}>
      <img src="/food4agent-mark.svg" alt="" width={40} height={40} className="size-10 shrink-0" />
      food4agent
    </a>
  );
}

export const siteNavLinks = [
  { href: "/skills", label: "技能" },
  { href: "/mcp", label: "MCP" },
  { href: "/login", label: "我的主页" },
] as const;

export function SiteHeader() {
  const session = useSession();
  return (
    <SiteHeaderBar>
      {siteNavLinks.map((item) => {
        const home = item.label === "我的主页";
        return (
          <a
            key={item.label}
            href={home ? accountHomeHref(session) : item.href}
            onClick={home ? (event) => followAccountHome(event, session) : undefined}
          >
            {item.label}
          </a>
        );
      })}
    </SiteHeaderBar>
  );
}

export function SiteHeaderBar({ children }: { children: ReactNode }) {
  return (
    <header className="sticky top-0 z-20 border-b-3 border-foreground bg-primary">
      <div className="px-4 md:px-8">
        <div className="mx-auto flex w-full max-w-[1440px] items-center justify-between gap-4 py-3">
          <BrandLogo />
          <nav className="flex items-center gap-4 text-base font-black uppercase">{children}</nav>
        </div>
      </div>
    </header>
  );
}
