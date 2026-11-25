import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn, safeHref } from "@/lib/utils";
import { ArrowRight, Sparkles } from "lucide-react";

export interface HeroCenteredProps {
  badge?: string;
  title: string;
  titleHighlight?: string;
  description: string;
  primaryAction?: { label: string; href?: string; onClick?: (event: { preventDefault(): void }) => void };
  secondaryAction?: { label: string; href?: string; onClick?: (event: { preventDefault(): void }) => void };
  className?: string;
}

export function HeroCentered({
  badge,
  title,
  titleHighlight,
  description,
  primaryAction,
  secondaryAction,
  className,
}: HeroCenteredProps) {
  return (
    <section className={cn("px-4 py-20 md:px-8", className)}>
      <div className="mx-auto max-w-4xl space-y-8 text-center">
        {badge && (
          <Badge variant="outline" className="px-4 py-1 text-sm">
            <Sparkles className="mr-2 h-3 w-3" />
            {badge}
          </Badge>
        )}

        <h1 className="text-4xl font-black tracking-tight md:text-5xl lg:text-6xl">
          {title}{" "}
          {titleHighlight && <span className="inline-block bg-primary px-2 text-primary-foreground">{titleHighlight}</span>}
        </h1>

        <p className="mx-auto max-w-2xl text-lg font-medium text-muted-foreground md:text-xl">{description}</p>

        {(primaryAction || secondaryAction) && (
          <div className="flex flex-col justify-center gap-4 sm:flex-row">
            {primaryAction &&
              (primaryAction.href ? (
                <Button size="lg" asChild>
                  <a href={safeHref(primaryAction.href)} onClick={primaryAction.onClick}>
                    {primaryAction.label}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              ) : (
                <Button size="lg" onClick={primaryAction.onClick}>
                  {primaryAction.label}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              ))}
            {secondaryAction &&
              (secondaryAction.href ? (
                <Button size="lg" variant="outline" asChild>
                  <a href={safeHref(secondaryAction.href)} onClick={secondaryAction.onClick}>{secondaryAction.label}</a>
                </Button>
              ) : (
                <Button size="lg" variant="outline" onClick={secondaryAction.onClick}>
                  {secondaryAction.label}
                </Button>
              ))}
          </div>
        )}
      </div>
    </section>
  );
}
