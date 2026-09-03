import type { Metadata } from "next";
import "./globals.css";
import DeskProvider from "@/components/DeskProvider";

export const metadata: Metadata = {
  title: "STONKS — Autonomous AI Options Trading Desk",
  description:
    "Strategic Trading & Orchestration Network for Knowledge-driven Systems: An autonomous multi-agent AI options desk executing defined-risk structures on Alpaca paper trading.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased bg-[#06080d] text-[#f5f7fa] min-h-screen relative selection:bg-cyan-500/20">
        <div className="ambient-glow" aria-hidden="true" />
        <DeskProvider>{children}</DeskProvider>
      </body>
    </html>
  );
}
