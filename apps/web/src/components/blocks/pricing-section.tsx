import { Check } from "lucide-react";
import { cn, safeHref } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export interface PricingTier {
  name: string;
  price: string;
  period?: string;
  description?: string;
  features: string[];
  cta?: string;
  ctaHref?: string;
  onCtaClick?: () => void;
  featured?: boolean;
}

export interface PricingSectionProps {
  title?: string;
  subtitle?: string;
  tiers: PricingTier[];
  className?: string;
}

export function PricingSection({ title = "Pricing", subtitle, tiers, className }: PricingSectionProps) {
  return (
    <section className={cn("px-4 py-16 md:px-8 lg:px-16", className)}>
      <div className="mx-auto max-w-6xl">
        <div className="mb-12 space-y-3 text-center">
          <h2 className="text-4xl font-black uppercase tracking-tight md:text-5xl">{title}</h2>
          {subtitle && <p className="mx-auto max-w-xl text-muted-foreground">{subtitle}</p>}
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {tiers.map((tier) => (
            <div
              key={tier.name}
              className={cn(
                "flex flex-col border-3 border-foreground bg-card p-6",
                tier.featured ? "shadow-[8px_8px_0px_hsl(var(--shadow-color))] md:-translate-y-2" : "shadow-[4px_4px_0px_hsl(var(--shadow-color))]",
              )}
            >
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-black uppercase tracking-wide">{tier.name}</h3>
                {tier.featured && <Badge variant="accent">多数用法</Badge>}
              </div>
              {tier.description && <p className="mt-2 text-sm text-muted-foreground">{tier.description}</p>}
              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-4xl font-black">{tier.price}</span>
                {tier.period && <span className="text-sm font-bold text-muted-foreground">/{tier.period}</span>}
              </div>
              <ul className="mt-6 flex-1 space-y-3">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm font-medium">
                    <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center border-2 border-foreground bg-success">
                      <Check className="h-3 w-3 text-success-foreground" />
                    </span>
                    {feature}
                  </li>
                ))}
              </ul>
              {tier.ctaHref ? (
                <Button className="mt-6 w-full" variant={tier.featured ? "default" : "outline"} asChild>
                  <a href={safeHref(tier.ctaHref)}>{tier.cta ?? "Get started"}</a>
                </Button>
              ) : (
                <Button className="mt-6 w-full" variant={tier.featured ? "default" : "outline"} onClick={tier.onCtaClick}>
                  {tier.cta ?? "Get started"}
                </Button>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
