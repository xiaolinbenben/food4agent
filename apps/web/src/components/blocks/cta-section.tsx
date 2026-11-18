import { Button } from "@/components/ui/button";
import { cn, safeHref } from "@/lib/utils";
import { ArrowRight } from "lucide-react";

export interface CTASimpleProps {
  title: string;
  description?: string;
  primaryAction: { label: string; href?: string; onClick?: () => void };
  secondaryAction?: { label: string; href?: string; onClick?: () => void };
  className?: string;
}

export function CTASimple({ title, description, primaryAction, secondaryAction, className }: CTASimpleProps) {
  return (
    <section className={cn("px-4 py-16 md:px-8 lg:px-16", className)}>
      <div className="mx-auto max-w-4xl space-y-6 text-center">
        <h2 className="text-3xl font-black uppercase tracking-tight md:text-4xl">{title}</h2>
        {description && <p className="mx-auto max-w-2xl text-lg font-medium text-muted-foreground">{description}</p>}
        <div className="flex flex-col justify-center gap-4 sm:flex-row">
          {primaryAction.href ? (
            <Button size="lg" asChild>
              <a href={safeHref(primaryAction.href)}>
                {primaryAction.label}
                <ArrowRight className="ml-2 h-4 w-4" />
              </a>
            </Button>
          ) : (
            <Button size="lg" onClick={primaryAction.onClick}>
              {primaryAction.label}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          )}
          {secondaryAction &&
            (secondaryAction.href ? (
              <Button size="lg" variant="outline" asChild>
                <a href={safeHref(secondaryAction.href)}>{secondaryAction.label}</a>
              </Button>
            ) : (
              <Button size="lg" variant="outline" onClick={secondaryAction.onClick}>
                {secondaryAction.label}
              </Button>
            ))}
        </div>
      </div>
    </section>
  );
}
