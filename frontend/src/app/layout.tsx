import type { Metadata, Viewport } from "next";
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

const siteUrl = "https://nabom.ponslink.com";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "나봄 — 기록할수록 선명해지는 나",
    template: "%s | 나봄",
  },
  description:
    "나봄은 매일의 기록과 회고를 통해 시간이 지날수록 선명해지는 나만의 Living Profile을 만드는 서비스입니다.",
  keywords: [
    "나봄",
    "NABOM",
    "자기기록",
    "성장",
    "회고",
    "자기이해",
    "Living Profile",
  ],
  authors: [{ name: "NABOM Team" }],
  creator: "NABOM Team",
  publisher: "NABOM",
  alternates: {
    canonical: "/",
  },
  icons: {
    icon: [{ url: "/icon.png", type: "image/png", sizes: "1254x1254" }],
    apple: [{ url: "/apple-icon.png", type: "image/png", sizes: "180x180" }],
  },
  openGraph: {
    title: "나봄 — 기록할수록 선명해지는 나",
    description:
      "오늘의 나는, 어제의 나와 조금 다르니까. 매일의 기록으로 나를 더 선명하게 만나보세요.",
    url: siteUrl,
    siteName: "나봄",
    locale: "ko_KR",
    type: "website",
    images: [
      {
        url: "/opengraph-image.png",
        width: 1200,
        height: 630,
        alt: "나봄 — 기록할수록 선명해지는 나",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "나봄 — 기록할수록 선명해지는 나",
    description: "매일의 기록으로 나를 더 선명하게 만나보세요.",
    images: ["/opengraph-image.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  themeColor: "#faf7f2",
  colorScheme: "light",
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
