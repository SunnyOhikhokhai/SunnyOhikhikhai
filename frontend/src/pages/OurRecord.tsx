import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { FileSearch, LayoutGrid, List, Search, SlidersHorizontal, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { RecordCard } from "@/components/shared/cards";
import { PageHeader } from "@/components/shared/PageHeader";
import { Pagination } from "@/components/shared/Pagination";
import { Seo } from "@/components/shared/Seo";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { VerificationBadge } from "@/components/shared/badges";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { CardSkeleton } from "@/components/ui/skeleton";
import { useDebounce } from "@/hooks/useDebounce";
import { useMeta } from "@/hooks/useMeta";
import { api, type Paged } from "@/lib/api";
import { VERIFICATION } from "@/lib/constants";
import type { RecordCard as RecordCardT, VerificationStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const FILTERS = ["area_council", "category", "year", "verification", "sort"] as const;

export default function OurRecord() {
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");
  const [view, setView] = useState<"grid" | "list">(() => {
    try {
      return (localStorage.getItem("nipam-record-view") as "grid" | "list") ?? "grid";
    } catch {
      return "grid";
    }
  });
  const [showFilters, setShowFilters] = useState(false);
  const debouncedQ = useDebounce(q, 350);
  const meta = useMeta();
  const page = Number(params.get("page") ?? 1);

  useEffect(() => {
    const next = new URLSearchParams(params);
    if (debouncedQ) next.set("q", debouncedQ);
    else next.delete("q");
    if ((params.get("q") ?? "") !== debouncedQ) {
      next.delete("page");
      setParams(next, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQ]);

  useEffect(() => {
    try {
      localStorage.setItem("nipam-record-view", view);
    } catch {
      /* ignore */
    }
  }, [view]);

  const query = Object.fromEntries([...params.entries()]);
  const { data, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ["records", query],
    queryFn: () => api.get<Paged<RecordCardT>>("/api/projects", { page_size: 12, ...query }),
    placeholderData: keepPreviousData,
  });

  const set = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    next.delete("page");
    setParams(next);
  };
  const activeCount = FILTERS.filter((f) => f !== "sort" && params.get(f)).length;
  const clear = () => {
    setQ("");
    setParams(new URLSearchParams());
  };

  const filterControls = (
    <>
      <Select aria-label="Area Council" value={params.get("area_council") ?? ""} onChange={(e) => set("area_council", e.target.value)}>
        <option value="">All Area Councils</option>
        {meta.data?.area_councils.map((c) => (
          <option key={c.slug} value={c.slug}>{c.name}</option>
        ))}
      </Select>
      <Select aria-label="Category" value={params.get("category") ?? ""} onChange={(e) => set("category", e.target.value)}>
        <option value="">All categories</option>
        {meta.data?.project_categories.map((c) => (
          <option key={c.slug} value={c.slug}>{c.name}</option>
        ))}
      </Select>
      <Select aria-label="Year" value={params.get("year") ?? ""} onChange={(e) => set("year", e.target.value)}>
        <option value="">Any year</option>
        {meta.data?.record_years.map((y) => (
          <option key={y} value={y}>{y}</option>
        ))}
      </Select>
      <Select aria-label="Verification status" value={params.get("verification") ?? ""} onChange={(e) => set("verification", e.target.value)}>
        <option value="">Any status</option>
        {Object.entries(VERIFICATION).map(([k, v]) => (
          <option key={k} value={k}>{v.label}</option>
        ))}
      </Select>
    </>
  );

  return (
    <>
      <Seo title="Our Record" description="Sen. Philip Aduda's record: a searchable library of documented projects and activities across the FCT, with sources." />
      <PageHeader
        eyebrow="Our Record"
        title="Sen. Philip Aduda's record"
        description="Documented projects and public activities across the FCT. Every record shows its sources and verification status, so supporters can share it with confidence."
        crumbs={[{ to: "/", label: "Home" }, { label: "Our Record" }]}
      >
        <div className="mt-8 flex flex-wrap gap-2">
          {(Object.keys(VERIFICATION) as VerificationStatus[]).map((s) => (
            <VerificationBadge key={s} status={s} className="bg-white" />
          ))}
        </div>
      </PageHeader>

      <div className="sticky top-16 z-30 border-b border-border bg-white/95 backdrop-blur lg:top-[72px]">
        <div className="container py-3">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search records by title, place or keyword" className="pl-10" aria-label="Search records" type="search" />
            </div>
            <Button variant="outline" className="lg:hidden" onClick={() => setShowFilters((s) => !s)} aria-expanded={showFilters}>
              <SlidersHorizontal /> <span className="sr-only sm:not-sr-only">Filters</span>
              {activeCount > 0 && <span className="rounded-full bg-green-600 px-1.5 text-[11px] text-white">{activeCount}</span>}
            </Button>
            <div className="hidden gap-2 lg:grid lg:w-[46rem] lg:grid-cols-4">{filterControls}</div>
          </div>
          {showFilters && <div className="mt-3 grid grid-cols-2 gap-2 lg:hidden">{filterControls}</div>}
        </div>
      </div>

      <section className="container py-8">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-muted-foreground" aria-live="polite">
            {data ? (
              <>
                <strong className="text-navy">{data.meta.total}</strong> record{data.meta.total === 1 ? "" : "s"}
                {isFetching && " · updating…"}
              </>
            ) : (
              "Loading records…"
            )}
            {(activeCount > 0 || q) && (
              <button onClick={clear} className="ml-3 inline-flex items-center gap-1 font-semibold text-green-600 hover:underline">
                <X className="size-3.5" /> Clear filters
              </button>
            )}
          </p>
          <div className="flex items-center gap-2">
            <Select aria-label="Sort" value={params.get("sort") ?? "recent"} onChange={(e) => set("sort", e.target.value === "recent" ? "" : e.target.value)} className="h-9 w-auto text-sm">
              <option value="recent">Recently added</option>
              <option value="year_desc">Year (newest)</option>
              <option value="year_asc">Year (oldest)</option>
              <option value="title">Title A–Z</option>
              <option value="popular">Most viewed</option>
            </Select>
            <div className="flex rounded-xl border border-border p-0.5" role="group" aria-label="View">
              {(["grid", "list"] as const).map((v) => (
                <button
                  key={v}
                  onClick={() => setView(v)}
                  aria-pressed={view === v}
                  aria-label={`${v} view`}
                  className={cn("rounded-lg p-1.5 transition", view === v ? "bg-navy text-white" : "text-slate-500 hover:text-navy")}
                >
                  {v === "grid" ? <LayoutGrid className="size-4" /> : <List className="size-4" />}
                </button>
              ))}
            </div>
          </div>
        </div>

        {error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : isLoading ? (
          <CardSkeleton count={6} />
        ) : !data?.data.length ? (
          <EmptyState
            icon={FileSearch}
            title="No records match your search"
            description="Try removing a filter or using a different keyword."
            action={<Button variant="outline" onClick={clear}>Clear all filters</Button>}
          />
        ) : (
          <div className={cn(view === "grid" ? "grid gap-6 sm:grid-cols-2 lg:grid-cols-3" : "space-y-4", isFetching && "opacity-70 transition-opacity")}>
            {data.data.map((r) => <RecordCard key={r.id} record={r} view={view} />)}
          </div>
        )}
        {data && (
          <Pagination
            page={page}
            totalPages={data.meta.total_pages}
            onChange={(p) => {
              set("page", String(p));
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          />
        )}
      </section>
    </>
  );
}
