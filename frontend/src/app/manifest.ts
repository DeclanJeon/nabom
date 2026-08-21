import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "나봄 — 기록할수록 선명해지는 나",
    short_name: "나봄",
    description:
      "매일의 기록과 회고를 통해 시간이 지날수록 선명해지는 나만의 Living Profile",
    start_url: "/",
    display: "standalone",
    background_color: "#faf7f2",
    theme_color: "#faf7f2",
    lang: "ko",
    icons: [
      {
        src: "/icon.png",
        sizes: "1254x1254",
        type: "image/png",
        purpose: "any maskable",
      },
      {
        src: "/apple-icon.png",
        sizes: "180x180",
        type: "image/png",
        purpose: "any",
      },
    ],
  };
}
