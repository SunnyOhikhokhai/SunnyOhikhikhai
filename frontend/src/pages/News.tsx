import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Newspaper, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { CoverArt } from "@/components/brand/Artwork";
import { ContentLabelBadge, DemoBadge } from "@/components/shared/badges";
import { NewsCard } from "@/components/shared/cards";
import { PageHeader } from "@/components/shared/PageHeader";
import { Pagination } from "@/components/shared/Pagination";
import { Seo } from "@/components/shared/Seo";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Input } from "@/components/ui/input";
import { CardSkeleton } from "@/components/ui/skeleton";
import { useDebounce } from "@/hooks/useDebounce";
import { useMeta } from "@/hooks/useMeta";
import { api, type Paged } from "@/lib/api";
import type { NewsCard as NewsCardT } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

export default function News() {
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");
  const dq = useDebounce(q, 350);
  const meta = useMeta();
  const category = params.get("category") ?? "";
  const page = Number(params.get("page") ?? 1);

  useEffect(() => {
    if ((params.get("q") ?? "") === dq) return;
    const next = new URLSearchParams(params);
    if (dq) next.set("q", dq);
    else next.delete("q");
    next.delete("page");
    setParams(next, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dq]);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["news", Object.fromEntries(params)],
    queryFn: () => api.get<Paged<NewsCardT>>("/api/news", { page_size: 9, ...Object.fromEntries(params) }),
    placeholderData: keepPreviousData,
  });

  const setCategory = (slug: string) => {
    const next = new URLSearchParams(params);
    if (slug) next.set("category", slug);
    else next.delete("category");
    next.delete("page");
    setParams(next);
  };
  const lead = page === 1 && !category && !dq ? data?.data[0] : undefined;
  const rest = lead ? data?.data.slice(1) : data?.data;

  return (
    <>
      <Seo title="News" description="NIPAM updates, community news, FCT news, events, announcements and public information." />
      <PageHeader eyebrow="News" title="News & announcements" description="Updates from NIPAM and communities across the Federal Capital Territory." crumbs={[{ to: "/", label: "Home" }, { label: "News" }]} />
      <div className="container py-8">
        <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 lg:mx-0 lg:px-0" role="tablist" aria-label="News categories">
            {[{ slug: "", name: "All" }, ...(meta.data?.news_categories ?? [])].map((c) => (
              <button
                key={c.slug}
                role="tab"
                aria-selected={category === c.slug}
                onClick={() => setCategory(c.slug)}
                className={cn(
                  "shrink-0 rounded-full px-4 py-2 text-sm font-semibold transition",
                  category === c.slug ? "bg-navy text-white" : "bg-surface text-slate-600 ring-1 ring-border hover:text-navy",
                )}
              >
                {c.name}
              </button>
            ))}
          </div>
          <div className="relative lg:w-72">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
            <Input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search news" className="pl-10" aria-label="Search news" />
          </div>
        </div>

        {error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : isLoading ? (
          <CardSkeleton count={6} />
        ) : !data?.data.length ? (
          <EmptyState icon={Newspaper} title="No articles found" description="Try another category or search term." />
        ) : (
          <>
            {lead && (
              <article className="group relative mb-10 grid overflow-hidden rounded-3xl border border-border bg-white shadow-card transition hover:shadow-lift lg:grid-cols-2">
                <div className="aspect-[16/9] overflow-hidden lg:aspect-auto">
                  {lead.image_url ? (
                    <img src={lead.image_url} alt={lead.image_alt ?? ""} className="size-full object-cover" />
                  ) : (
                    <CoverArt seed={lead.slug} icon="news" className="size-full min-h-[16rem]" />
                  )}
                </div>
                <div className="flex flex-col justify-center gap-3 p-6 sm:p-10">
                  <div className="flex flex-wrap gap-2">
                    <ContentLabelBadge label={lead.content_label} />
                    {lead.is_demo && <DemoBadge />}
                  </div>
                  <h2 className="text-2xl font-extrabold leading-tight sm:text-3xl">
                    <Link to={`/news/${lead.slug}`} className="after:absolute after:inset-0">{lead.title}</Link>
                  </h2>
                  <p className="text-muted-foreground">{lead.excerpt}</p>
                  <p className="text-sm text-slate-500">
                    {lead.category.name} · {lead.author_name} · {formatDate(lead.published_at)}
                  </p>
                </div>
              </article>
            )}
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">{rest?.map((n) => <NewsCard key={n.id} item={n} />)}</div>
          </>
        )}
        {data && <Pagination page={page} totalPages={data.meta.total_pages} onChange={(p) => { const n = new URLSearchParams(params); n.set("page", String(p)); setParams(n); window.scrollTo({ top: 0 }); }} />}
      </div>
    </>
  );
}
