import type { ReactNode } from "react";
import { cn, safeHref } from "@/lib/utils";

export interface FooterLink {
  label: string;
  href: string;
  onClick?: (event: { preventDefault(): void }) => void;
}

export interface FooterSimpleProps {
  logo?: ReactNode;
  links?: FooterLink[];
  copyright?: string;
  className?: string;
}

export function FooterSimple({ logo, links, copyright = `© ${new Date().getFullYear()} food4agent`, className }: FooterSimpleProps) {
  return (
    <footer className={cn("border-t-3 border-foreground px-4 py-12 md:px-8", className)}>
      <div className="mx-auto w-full max-w-[1440px] space-y-6 text-center">
        {logo && <div className="text-2xl font-black uppercase">{logo}</div>}
        {links && (
          <nav className="flex flex-wrap justify-center gap-6">
            {links.map((link) => (
              <a key={link.label} href={safeHref(link.href)} onClick={link.onClick} className="text-base font-black uppercase text-muted-foreground transition-colors hover:text-foreground">
                {link.label}
              </a>
            ))}
          </nav>
        )}
        <p className="text-sm text-muted-foreground">{copyright}</p>
      </div>
    </footer>
  );
}
