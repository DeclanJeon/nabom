import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: "https://nabom.ponslink.com/",
      changeFrequency: "weekly",
      priority: 1,
    },
  ];
}
