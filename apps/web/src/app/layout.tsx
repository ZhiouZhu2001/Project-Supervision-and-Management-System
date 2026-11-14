import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Project Supervision",
  description: "Record what you actually did, and be told when you did not.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-dvh">{children}</body>
    </html>
  );
}
