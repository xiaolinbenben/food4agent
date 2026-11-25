import * as React from "react";
import { cn } from "@/lib/utils";

const Textarea = React.forwardRef<HTMLTextAreaElement, React.ComponentProps<"textarea">>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "flex min-h-28 w-full border-3 border-foreground bg-background px-3 py-2 text-sm font-medium shadow-[4px_4px_0px_hsl(var(--shadow-color))] outline-none placeholder:text-muted-foreground focus:bg-accent disabled:opacity-50",
      className,
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";

export { Textarea };
