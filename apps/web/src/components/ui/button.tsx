import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";

import { cn } from "@/lib/utils";

/**
 * shadcn/ui button, re-themed with the Daymark tokens. The variants keep
 * shadcn's names so `npx shadcn add` output stays interchangeable; the values
 * come from spec 0002 rather than from the default neutral palette.
 */
const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-[9px] whitespace-nowrap rounded-[7px] border text-[13px] font-[550] transition-colors duration-[160ms] disabled:pointer-events-none disabled:opacity-50 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/90",
        secondary: "border-border bg-card text-foreground hover:bg-secondary",
        subtle: "border-border bg-transparent text-muted-foreground hover:bg-secondary",
        ghost: "border-transparent text-muted-foreground hover:bg-secondary",
        link: "border-transparent text-accent-foreground underline-offset-4 hover:underline",
      },
      size: {
        default: "min-h-[44px] px-[17px] py-[10px]",
        sm: "min-h-[36px] px-3 text-[12px]",
        icon: "h-[30px] w-[30px] min-h-0 border-border p-0 text-muted-foreground hover:bg-secondary",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export type ButtonProps = React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & { asChild?: boolean };

export function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: ButtonProps) {
  const Component = asChild ? Slot : "button";
  return (
    <Component className={cn(buttonVariants({ variant, size, className }))} {...props} />
  );
}

export { buttonVariants };
