import type * as React from "react";

import { cn } from "@/lib/utils";

/**
 * A native select, styled to match Input.
 *
 * shadcn's Select is a Radix popover with its own positioning layer; for a
 * single-option project picker that would add a portal, a scroll lock and
 * keyboard handling to reproduce what the platform already does better on a
 * phone. Same tokens, same height, no extra surface.
 */
export function Select({ className, ...props }: React.ComponentProps<"select">) {
  return (
    <select
      className={cn(
        "min-h-[46px] w-full appearance-none rounded-[7px] border border-field-line bg-white bg-[url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2212%22 height=%2212%22 fill=%22none%22 stroke=%22%23697069%22 stroke-width=%221.65%22 stroke-linecap=%22round%22 stroke-linejoin=%22round%22><path d=%22m2 4.5 4 4 4-4%22/></svg>')] bg-[length:12px] bg-[right_13px_center] bg-no-repeat px-[13px] py-[11px] pr-9 text-[14px] text-foreground disabled:cursor-not-allowed disabled:opacity-50 max-[700px]:text-[16px]",
        className,
      )}
      {...props}
    />
  );
}
