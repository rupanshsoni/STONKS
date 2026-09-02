import type { Metadata } from "next";
import "./globals.css";
import DeskProvider from "@/components/DeskProvider";

export const metadata: Metadata = {
  title: "STONKS — autonomous AI options desk",
  description:
    "Strategic Trading & Orchestration Network for Knowledge-driven Systems: an autonomous multi-agent options desk on Alpaca paper trading.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <DeskProvider>{children}</DeskProvider>
      </body>
    </html>
  );
}
