import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "CBSE AI Doubt Solver | Classes 6–12",
  description:
    "AI-powered CBSE doubt solver for Science and Social Science. Ask doubts via text, voice, or photo of your textbook.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="h-full">{children}</body>
    </html>
  );
}
