import { Helmet } from "react-helmet-async";

interface SeoProps {
  title?: string;
  description?: string;
  image?: string | null;
  type?: "website" | "article";
  noindex?: boolean;
  jsonLd?: Record<string, unknown>;
}

const DEFAULT_DESC =
  "NIPAM — Non-Indigenes for Philip Aduda Movement — the support movement for Sen. Philip Aduda across the Federal Capital Territory.";

export function Seo({ title, description = DEFAULT_DESC, image, type = "website", noindex, jsonLd }: SeoProps) {
  const full = title ? `${title} | NIPAM` : "NIPAM — Non-Indigenes for Philip Aduda Movement";
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const url = typeof window !== "undefined" ? origin + window.location.pathname : "";
  const img = image ? (image.startsWith("http") ? image : origin + image) : `${origin}/og-image.png`;
  return (
    <Helmet>
      <title>{full}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={url} />
      <meta property="og:title" content={full} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content={type} />
      <meta property="og:url" content={url} />
      <meta property="og:image" content={img} />
      <meta name="twitter:title" content={full} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={img} />
      {noindex && <meta name="robots" content="noindex,nofollow" />}
      {jsonLd && <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>}
    </Helmet>
  );
}
