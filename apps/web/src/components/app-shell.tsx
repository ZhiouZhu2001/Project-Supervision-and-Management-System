"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AccountBar } from "@/components/account-bar";
import { Brand, Icon } from "@/components/icon";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="app-frame">
      <a href="#content" className="skip-link">
        Skip to content
      </a>
      <aside className="sidebar">
        <Link href="/" className="brand-link" aria-label="Daymark home">
          <Brand />
        </Link>
        <div className="sidebar-label">YOUR SPACE</div>
        <nav aria-label="Main navigation" className="main-nav">
          <Link href="/" aria-current={pathname === "/" ? "page" : undefined}>
            <Icon name="today" />
            Today
            <Icon name="arrow" size={16} />
          </Link>
          <Link
            href="/projects"
            aria-current={pathname.startsWith("/projects") ? "page" : undefined}
          >
            <Icon name="projects" />
            Projects
            <Icon name="arrow" size={16} />
          </Link>
        </nav>
        <div className="sidebar-note">
          <span className="tiny-label">ONE DAY AT A TIME</span>
          <p>
            Small actions.
            <br />
            Something to show for them.
          </p>
          <span className="note-line" />
        </div>
        <AccountBar />
      </aside>
      <div className="workspace">
        <header className="workspace-top">
          <span>
            Personal workspace <span className="top-divider">/</span>{" "}
            <strong>
              {pathname.startsWith("/projects") ? "Projects" : "Today"}
            </strong>
          </span>
          <span className="private-label">
            <Icon name="lock" size={13} /> Only you
          </span>
        </header>
        <main id="content" className="page-content">
          {children}
        </main>
        <footer className="workspace-footer">
          <span>Make a mark. Keep going.</span>
          <span>
            Europe/Madrid <span className="footer-dot">·</span> Business day
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
    <header className="page-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="page-description">{description}</p>
      </div>
      {action}
    </header>
  );
}

export function LoadingProjects() {
  return (
    <div className="loading-list" role="status">
      <span className="sr-only">Loading projects…</span>
      {[1, 2, 3].map((n) => (
        <div className="skeleton-row" key={n}>
          <span />
          <div>
            <i />
            <i />
          </div>
        </div>
      ))}
    </div>
  );
}
