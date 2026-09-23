import { SearchX, Search as SearchIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useSearch } from "@/components/layout/GlobalSearch";
import { DiscussionRow, EventCard, NewsCard, RecordCard } from "@/components/shared/cards";
import { PageHeader } from "@/components/shared/PageHeader";
import { Seo } from "@/components/shared/Seo";
import { EmptyState } from "@/components/shared/states";
import { Input } from "@/components/ui/input";
import { CardSkeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const TYPES = [
  ["", "All"],
  ["records", "Records"],
  ["news", "News"],
  ["events", "Events"],
  ["councils", "Area Councils"],
  ["discussions", "Community"],
] as const;

export default function SearchPage() {
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");
  const type = params.get("type") ?? "";
  const { data, isFetching } = useSearch(q, type ? 20 : 6, type || undefined);
  useEffect(() => {
    const t = setTimeout(() => {
      const n = new URLSearchParams(params);
      if (q) n.set("q", q);
      else n.delete("q");
      setParams(n, { replace: true });
    }, 400);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);
  const r = data?.data;
  const section = (title: string, count: number, children: React.ReactNode) =>
    count ? (
      <section className="mb-12">
        <h2 className="mb-5 text-xl font-extrabold">{title} <span className="text-base font-semibold text-muted-foreground">({count})</span></h2>
        {children}
      </section>
    ) : null;

  return (
    <>
      <Seo title={q ? `Search: ${q}` : "Search"} noindex />
      <PageHeader eyebrow="Search" title="Search NIPAM" crumbs={[{ to: "/", label: "Home" }, { label: "Search" }]}>
        <div className="relative mt-8 max-w-2xl">
          <SearchIcon className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-slate-400" />
          <Input autoFocus type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search records, news, events, councils and discussions" className="h-14 pl-12 text-base" aria-label="Search" />
        </div>
      </PageHeader>
      <div className="container py-8">
        <div className="no-scrollbar -mx-4 mb-8 flex gap-2 overflow-x-auto px-4">
          {TYPES.map(([k, label]) => (
            <button key={k} onClick={() => { const n = new URLSearchParams(params); if (k) n.set("type", k); else n.delete("type"); setParams(n); }} aria-pressed={type === k} className={cn("shrink-0 rounded-full px-4 py-2 text-sm font-semibold", type === k ? "bg-navy text-white" : "bg-surface text-slate-600 ring-1 ring-border")}>
              {label}
            </button>
          ))}
        </div>
        {q.trim().length < 2 ? (
          <EmptyState icon={SearchIcon} title="Start typing to search" description="Search across Our Record, news, events, Area Councils and community discussions." />
        ) : !data && isFetching ? (
          <CardSkeleton />
        ) : !data?.meta.total ? (
          <EmptyState
            icon={SearchX}
            title={`No results for “${q}”`}
            description={<>Check the spelling or try a broader term. You can also browse <Link to="/our-record" className="font-semibold text-green-600">Our Record</Link> or <Link to="/news" className="font-semibold text-green-600">News</Link>.</>}
          />
        ) : (
          r && (
            <div aria-live="polite">
              {section("Area Councils", r.councils?.length ?? 0, (
                <div className="flex flex-wrap gap-3">
                  {r.councils?.map((c) => <Link key={c.slug} to={`/area-councils/${c.slug}`} className="rounded-xl border border-border bg-white px-5 py-3 font-semibold text-navy shadow-card hover:border-green-500">{c.name}</Link>)}
                </div>
              ))}
              {section("Our Record", r.records?.length ?? 0, <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">{r.records?.map((x) => <RecordCard key={x.id} record={x} />)}</div>)}
              {section("News", r.news?.length ?? 0, <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">{r.news?.map((x) => <NewsCard key={x.id} item={x} />)}</div>)}
              {section("Events", r.events?.length ?? 0, <div className="grid gap-4 md:grid-cols-2">{r.events?.map((x) => <EventCard key={x.id} event={x} />)}</div>)}
              {section("Community", r.discussions?.length ?? 0, <div className="space-y-4">{r.discussions?.map((x) => <DiscussionRow key={x.id} d={x} />)}</div>)}
            </div>
          )
        )}
      </div>
    </>
  );
}
