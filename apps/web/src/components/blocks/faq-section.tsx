import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { cn } from "@/lib/utils";

export interface FAQItem {
  question: string;
  answer: string;
}

export interface FAQAccordionProps {
  title?: string;
  subtitle?: string;
  description?: string;
  items: FAQItem[];
  className?: string;
}

export function FAQAccordion({ title, subtitle, description, items, className }: FAQAccordionProps) {
  return (
    <section className={cn("px-4 py-16 md:px-8 lg:px-16", className)}>
      <div className="mx-auto max-w-3xl">
        {(title || subtitle || description) && (
          <div className="mb-12 space-y-4 text-center">
            {subtitle && <p className="text-sm font-bold uppercase tracking-widest text-primary">{subtitle}</p>}
            {title && <h2 className="text-3xl font-black uppercase tracking-tight md:text-4xl">{title}</h2>}
            {description && <p className="text-lg font-medium text-muted-foreground">{description}</p>}
          </div>
        )}

        <Accordion type="single" collapsible className="space-y-4">
          {items.map((item, index) => (
            <AccordionItem
              key={item.question}
              value={`item-${index}`}
              className="border-3 border-foreground bg-card shadow-[4px_4px_0px_hsl(var(--shadow-color))] transition data-[state=open]:translate-x-[-2px] data-[state=open]:translate-y-[-2px] data-[state=open]:shadow-[6px_6px_0px_hsl(var(--shadow-color))]"
            >
              <AccordionTrigger className="px-6 py-4 font-bold uppercase tracking-wide hover:no-underline">{item.question}</AccordionTrigger>
              <AccordionContent className="px-6 pb-4 text-muted-foreground">{item.answer}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
