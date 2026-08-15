import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "나봄 — 기록할수록 선명해지는 나",
  description:
    "여러 입력과 실제 삶의 기록을 통해 시간에 따라 변화하는 한 사람의 Living Profile을 만드는 서비스",
  keywords: ["나봄", "NABOM", "자기기록", "성장", "회고", "자기이해"],
  authors: [{ name: "NABOM Team" }],
  openGraph: {
    title: "나봄 — 기록할수록 선명해지는 나",
    description: "오늘의 나는, 어제의 나와 조금 다르니까.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        {children}
        <Toaster position="top-center" richColors />
      </body>
    </html>
  );
}
