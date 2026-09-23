import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Info } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { ContentLabelBadge, DemoBadge } from "@/components/shared/badges";
import { NewsCard } from "@/components/shared/cards";
import { Markdown } from "@/components/shared/Markdown";
import { Seo } from "@/components/shared/Seo";
import { ShareButton } from "@/components/shared/Share";
import { ErrorState } from "@/components/shared/states";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, getData } from "@/lib/api";
import type { NewsDetail as NewsDetailT } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import NotFound from "./NotFound";

export default function NewsDetail() {
  const { slug = "" } = useParams();
  const { data: n, isLoading, error, refetch } = useQuery({ queryKey: ["news", slug], queryFn: () => getData<NewsDetailT>(`/api/news/${slug}`) });
  if (error instanceof ApiError && error.status === 404) return <NotFound />;
  if (error) return <div className="container py-16"><ErrorState error={error} onRetry={() => refetch()} /></div>;
  if (isLoading || !n)
    return (
      <div className="container max-w-3xl space-y-5 py-14">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="aspect-[16/9]" />
      </div>
    );
  return (
    <article>
      <Seo
        title={n.title}
        description={n.excerpt}
        image={n.image_url}
        type="article"
        jsonLd={{ "@context": "https://schema.org", "@type": "NewsArticle", headline: n.title, datePublished: n.published_at, dateModified: n.updated_at, author: { "@type": "Organization", name: n.author_name }, publisher: { "@type": "Organization", name: "NIPAM" } }}
      />
      <header className="container max-w-3xl pb-8 pt-10 sm:pt-14">
        <Link to="/news" className="inline-flex items-center gap-1.5 text-sm font-semibold text-green-600 hover:gap-2.5">
          <ArrowLeft className="size-4" /> All news
        </Link>
        <div className="mt-6 flex flex-wrap gap-2">
          <Badge variant="outline">{n.category.name}</Badge>
          <ContentLabelBadge label={n.content_label} />
          {n.area_council && <Badge>{n.area_council.name}</Badge>}
          {n.is_demo && <DemoBadge />}
        </div>
        <h1 className="mt-4 text-3xl font-extrabold leading-tight sm:text-4xl lg:text-[2.75rem]">{n.title}</h1>
        <p className="mt-4 text-lg text-muted-foreground">{n.excerpt}</p>
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-y border-border py-4">
          <p className="text-sm text-slate-600">
            Published by <strong className="text-navy">{n.author_name}</strong> · <time dateTime={n.published_at ?? undefined}>{formatDate(n.published_at, { day: "numeric", month: "long", year: "numeric" })}</time>
          </p>
          <ShareButton title={n.title} text={n.excerpt} />
        </div>
      </header>
      {n.image_url && (
        <div className="container max-w-4xl">
          <img src={n.image_url} alt={n.image_alt ?? ""} className="aspect-[16/9] w-full rounded-2xl object-cover" />
        </div>
      )}
      <div className="container max-w-3xl py-8">
        <Markdown>{n.body}</Markdown>
        {n.source_note && (
          <p className="mt-8 flex gap-2 rounded-xl bg-surface p-4 text-sm text-slate-600 ring-1 ring-border">
            <Info className="mt-0.5 size-4 shrink-0 text-green-600" />
            <span><strong className="text-navy">Source:</strong> {n.source_note}</span>
          </p>
        )}
        {n.content_label === "opinion" && (
          <p className="mt-4 text-sm italic text-slate-500">This article is opinion and reflects the views of its author.</p>
        )}
      </div>
      {n.related && n.related.length > 0 && (
        <section className="border-t border-border bg-surface py-14">
          <div className="container">
            <h2 className="mb-8 text-2xl font-extrabold">Related content</h2>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">{n.related.map((r) => <NewsCard key={r.id} item={r} />)}</div>
          </div>
        </section>
      )}
    </article>
  );
}
