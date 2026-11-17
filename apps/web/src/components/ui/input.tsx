import type * as React from "react";

import { cn } from "@/lib/utils";

export function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      className={cn(
        "min-h-[46px] w-full rounded-[7px] border border-[#d6d9ce] bg-white px-[13px] py-[11px] text-[14px] text-foreground placeholder:text-muted-foreground/70 disabled:cursor-not-allowed disabled:opacity-50 max-[700px]:text-[16px]",
        className,
      )}
      {...props}
    />
  );
}
