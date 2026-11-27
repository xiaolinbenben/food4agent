import { useLayoutEffect, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type SkillCategoryOption = { id: string; label: string; count: number };

export function catalogHref(pathname: string, page: number, categoryId = "", query = "") {
  const params = new URLSearchParams();
  if (categoryId) params.set("category", categoryId);
  if (query) params.set("q", query);
  if (page > 1) params.set("page", String(page));
  const search = params.toString();
  return search ? `${pathname}?${search}` : pathname;
}

export function SkillCategoryNav({ options, pathname, selectedId, query, className }: { options: SkillCategoryOption[]; pathname: string; selectedId: string | null; query: string; className?: string }) {
  const containerRef = useRef<HTMLElement>(null);
  const measureRef = useRef<HTMLDivElement>(null);
  const [visibleCount, setVisibleCount] = useState(0);
  const [expandedCount, setExpandedCount] = useState(0);
  const signature = options.map((item) => `${item.id}:${item.count}:${item.label}`).join("|");

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
  }, [signature]);

  const shownCount = Math.min(visibleCount + expandedCount, options.length);
  return (
    <nav ref={containerRef} aria-label="技能分类" className={cn("relative mb-6 flex flex-wrap items-center gap-3", className)}>
      <div aria-hidden="true" className="pointer-events-none invisible absolute inset-0 overflow-hidden">
        <div ref={measureRef} className="flex w-max gap-3">
          {options.map((item) => (
            <span key={item.id || "all"} className={buttonVariants({ variant: "outline", size: "sm" })}>
              {item.label}<span className="tabular-nums opacity-70">{item.count}</span>
            </span>
          ))}
          <span className={buttonVariants({ variant: "outline", size: "sm" })}>更多<ChevronDown /></span>
        </div>
      </div>
      {options.slice(0, shownCount).map((item) => (
        <Button key={item.id || "all"} size="sm" variant={selectedId === item.id ? "default" : "outline"} className="shrink-0" asChild>
          <a href={catalogHref(pathname, 1, item.id, query)} aria-current={selectedId === item.id ? "page" : undefined}>
            {item.label}<span className="tabular-nums opacity-70">{item.count}</span>
          </a>
        </Button>
      ))}
      {shownCount < options.length && (
        <Button size="sm" variant={options.slice(shownCount).some((item) => item.id === selectedId) ? "default" : "outline"} className="shrink-0" onClick={() => setExpandedCount((count) => count + 10)}>
          更多<ChevronDown />
        </Button>
      )}
    </nav>
  );
}
