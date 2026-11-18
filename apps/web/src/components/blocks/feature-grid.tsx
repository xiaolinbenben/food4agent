import type { ReactNode } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const featureColors = ["bg-primary/10", "bg-secondary/10", "bg-accent/10", "bg-green-500/10", "bg-yellow-500/10", "bg-blue-500/10"];
const iconColors = ["bg-primary", "bg-secondary", "bg-accent", "bg-green-500", "bg-yellow-500", "bg-blue-500"];

export interface FeatureItem {
  icon: ReactNode;
  title: string;
  description: string;
}

export interface FeatureGridWithIconsProps {
  title?: string;
  subtitle?: string;
  description?: string;
  features: FeatureItem[];
  columns?: 2 | 3 | 4;
  className?: string;
}

export function FeatureGridWithIcons({ title, subtitle, description, features, columns = 3, className }: FeatureGridWithIconsProps) {
  const gridCols = {
    2: "md:grid-cols-2",
    3: "md:grid-cols-2 lg:grid-cols-3",
    4: "md:grid-cols-2 lg:grid-cols-4",
  };

  return (
    <section className={cn("px-4 py-16 md:px-8 lg:px-16", className)}>
      <div className="mx-auto max-w-7xl">
        {(title || subtitle || description) && (
          <div className="mb-12 space-y-4 text-center">
            {subtitle && <p className="text-sm font-bold uppercase tracking-widest text-primary">{subtitle}</p>}
            {title && <h2 className="text-3xl font-black uppercase tracking-tight md:text-4xl">{title}</h2>}
            {description && <p className="mx-auto max-w-2xl text-lg font-medium text-muted-foreground">{description}</p>}
          </div>
        )}

        <div className={cn("grid gap-6", gridCols[columns])}>
          {features.map((feature, index) => (
            <Card
              key={feature.title}
              className={cn(
                "group transition hover:translate-x-[-4px] hover:translate-y-[-4px] hover:shadow-[8px_8px_0px_hsl(var(--shadow-color))]",
                featureColors[index % 6],
              )}
            >
              <CardHeader>
                <div
                  className={cn(
                    "mb-4 flex h-14 w-14 items-center justify-center border-3 border-foreground shadow-[3px_3px_0px_hsl(var(--shadow-color))]",
                    iconColors[index % 6],
                  )}
                >
                  {feature.icon}
                </div>
                <CardTitle className="uppercase">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base">{feature.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
