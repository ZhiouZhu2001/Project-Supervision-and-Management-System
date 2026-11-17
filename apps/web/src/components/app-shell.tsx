"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { AccountBar } from "@/components/account-bar";
import { Brand, Icon } from "@/components/icon";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Today", icon: "today" as const },
  { href: "/projects", label: "Projects", icon: "projects" as const },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-dvh">
      <a
        href="#content"
        className="sr-only rounded-[7px] bg-card px-3 py-2 text-[13px] focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50"
      >
        Skip to content
      </a>

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-20 flex w-[238px] flex-col border-r border-border bg-secondary px-[22px] pb-5 pt-9",
          "max-[1150px]:w-[210px] max-[1150px]:px-[17px]",
          "max-[700px]:static max-[700px]:w-full max-[700px]:border-b max-[700px]:border-r-0 max-[700px]:px-[22px] max-[700px]:pb-0 max-[700px]:pt-5",
        )}
      >
        <Link href="/" aria-label="Daymark home">
          <Brand />
        </Link>

        <div className="mb-[10px] mt-[26px] text-[10px] font-[600] tracking-[1.6px] text-muted-foreground max-[700px]:hidden">
          YOUR SPACE
        </div>

        <nav
          aria-label="Main navigation"
          className="flex flex-col gap-[2px] max-[700px]:mt-[19px] max-[700px]:flex-row max-[700px]:gap-2 max-[700px]:pb-3"
        >
          {NAV.map((item) => {
            const active =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex min-h-[48px] items-center gap-[13px] rounded-[8px] px-[14px] py-3 text-[14px] text-[#60675f] transition-colors duration-[160ms] hover:bg-[#e9ece0]/60",
                  active && "bg-[#e9ece0] font-[600] text-foreground",
                  "max-[700px]:min-h-[44px] max-[700px]:px-4 max-[700px]:py-2",
                )}
              >
                <Icon name={item.icon} />
                {item.label}
                <Icon
                  name="arrow"
                  size={16}
                  style={{ marginLeft: "auto" }}
                />
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto flex flex-col gap-[10px] max-[700px]:hidden">
          <span className="text-[10px] font-[600] tracking-[1.6px] text-muted-foreground">
            ONE DAY AT A TIME
          </span>
          <p className="font-serif text-[22px] leading-[1.35] tracking-[-0.3px] text-foreground">
            Small actions.
            <br />
            Something to show for them.
          </p>
          <span className="block h-[2px] w-[34px] bg-accent-foreground" />
        </div>

        <div className="mt-[26px] max-[700px]:hidden">
          <AccountBar />
        </div>
      </aside>

      <div
        className={cn(
          "ml-[238px] flex min-h-dvh flex-col",
          "max-[1150px]:ml-[210px] max-[700px]:ml-0",
        )}
      >
        <header className="flex h-20 items-center justify-between gap-4 border-b border-border px-[46px] text-[12px] text-muted-foreground max-[1150px]:px-7 max-[700px]:h-[55px] max-[700px]:px-[22px]">
          <span>
            Personal workspace <span className="opacity-40">/</span>{" "}
            <strong className="font-[600] text-foreground">
              {pathname.startsWith("/projects") ? "Projects" : "Today"}
            </strong>
          </span>
          <span className="inline-flex items-center gap-[6px]">
            <Icon name="lock" size={13} /> Only you
          </span>
        </header>

        <main
          id="content"
          className="mx-auto w-full max-w-[1320px] flex-1 px-[46px] pb-16 pt-[43px] max-[1150px]:px-7 max-[700px]:px-[22px] max-[700px]:pb-10 max-[700px]:pt-[29px]"
        >
          {children}
        </main>

        <footer className="flex justify-between gap-4 border-t border-border px-[46px] py-[19px] text-[10px] text-muted-foreground max-[1150px]:px-7 max-[700px]:flex-col max-[700px]:gap-[5px] max-[700px]:px-[22px] max-[700px]:py-[18px]">
          <span>Make a mark. Keep going.</span>
          <span>
            Europe/Madrid <span className="opacity-50">·</span> Business day
            starts at 04:00
          </span>
        </footer>
      </div>
    </div>
  );
}

export function PageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <header className="mb-[34px] flex flex-wrap items-start justify-between gap-4 max-[700px]:mb-6 max-[700px]:gap-4">
      <div className="min-w-0">
        <p className="mb-[10px] text-[10px] font-[650] tracking-[2px] text-accent-foreground">
          {eyebrow}
        </p>
        <h1 className="text-[34px] font-[650] leading-[1.1] tracking-[-1px] text-foreground max-[700px]:text-[32px]">
          {title}
        </h1>
        <p className="mt-2 max-w-[54ch] text-[14px] text-muted-foreground max-[700px]:text-[13px]">
          {description}
        </p>
      </div>
      {action}
    </header>
  );
}

export function LoadingProjects() {
  return (
    <div className="flex flex-col gap-2" role="status">
      <span className="sr-only">Loading projects…</span>
      {[1, 2, 3].map((n) => (
        <div
          key={n}
          className="flex animate-pulse items-center gap-[15px] rounded-[10px] border border-border bg-card px-5 py-[22px]"
        >
          <span className="h-[44px] w-[42px] shrink-0 rounded-[10px] bg-sage" />
          <div className="flex flex-1 flex-col gap-2">
            <span className="h-[11px] w-1/3 rounded bg-secondary" />
            <span className="h-[10px] w-2/3 rounded bg-secondary" />
          </div>
        </div>
      ))}
    </div>
  );
}
