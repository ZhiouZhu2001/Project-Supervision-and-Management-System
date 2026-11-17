import type * as React from "react";

import { cn } from "@/lib/utils";

export function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "min-h-[46px] w-full resize-y rounded-[7px] border border-[#d6d9ce] bg-white px-[13px] py-[11px] text-[14px] text-foreground placeholder:text-muted-foreground/70 disabled:cursor-not-allowed disabled:opacity-50 max-[700px]:text-[16px]",
        className,
      )}
      {...props}
    />
  );
}
