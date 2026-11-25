import * as React from "react";
import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "flex h-11 w-full border-3 border-foreground bg-background px-3 text-sm font-medium shadow-[4px_4px_0px_hsl(var(--shadow-color))] outline-none placeholder:text-muted-foreground focus:bg-accent disabled:opacity-50",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";

export { Input };
