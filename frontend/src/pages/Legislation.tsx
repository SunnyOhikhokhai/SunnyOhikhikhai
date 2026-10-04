import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { FileSearch, Gavel, Search, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { StageBadge, VerificationBadge } from "@/components/shared/badges";
import { PageHeader } from "@/components/shared/PageHeader";
import { Pagination } from "@/components/shared/Pagination";
import { Seo } from "@/components/shared/Seo";
import { RecordTabs } from "@/components/shared/SourceLine";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { CardSkeleton } from "@/components/ui/skeleton";
import { useDebounce } from "@/hooks/useDebounce";
import { useMeta } from "@/hooks/useMeta";
import { api, type Paged } from "@/lib/api";
import { LEGISLATIVE_STAGES, VERIFICATION } from "@/lib/constants";
import type { LegislationRecord as LegislationRecordT, LegislativeStage } from "@/lib/types";
import { cn } from "@/lib/utils";

const FILTERS = ["category", "year", "stage", "verification"] as const;

export function LegislationCard({ r }: { r: LegislationRecordT }) {
  const src = r.sources[0];
  return (
    <article className="group relative flex flex-col gap-3 rounded-2xl border border-border bg-white p-5 shadow-card transition hover:-translate-y-0.5 hover:shadow-lift focus-within:ring-2 focus-within:ring-green-500">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-green-600">{r.category}</span>
        {r.bill_number && <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">{r.bill_number}</span>}
        {r.year && <span className="text-xs text-slate-500">{r.year}</span>}
      </div>
      <h3 className="text-lg font-bold leading-snug">
        <Link to={`/legislation/${r.slug}`} className="after:absolute after:inset-0">
          {r.title}
        </Link>
      </h3>
      <p className="line-clamp-2 text-sm text-muted-foreground">{r.description}</p>
      <div className="flex flex-wrap gap-2">
        <StageBadge stage={r.legislative_stage} />
        <VerificationBadge status={r.verification_status} />
      </div>
      <p className="mt-auto border-t border-border pt-3 text-[13px] text-slate-500">Source: {src ? src.name : "Information pending verification."}</p>
    </article>
  );
}

export default function Legislation() {
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");
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

  const query = Object.fromEntries([...params.entries()]);
  const { data, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ["legislation", query],
    queryFn: () => api.get<Paged<LegislationRecordT>>("/api/legislation", { page_size: 20, ...query }),
    placeholderData: keepPreviousData,
  });

  const set = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    next.delete("page");
    setParams(next);
  };
  const active = FILTERS.filter((f) => params.get(f)).length;
  const clear = () => {
    setQ("");
    setParams(new URLSearchParams());
  };

  return (
    <>
      <Seo
        title="Legislation"
        description="Bills and legislative proposals associated with Senator Philip Tanimu Aduda, each shown at the stage its source documents."
      />
      <PageHeader
        eyebrow="Our Record"
        title="Legislative record"
        description="Each bill is a separate record showing the stage its source documents — introduced, second reading, committee stage and so on. A bill is never shown as law without an official enactment or assent record."
        crumbs={[{ to: "/", label: "Home" }, { to: "/our-record", label: "Our Record" }, { label: "Legislation" }]}
      >
        <RecordTabs />
      </PageHeader>

      <div className="z-30 border-b border-border bg-white/95 backdrop-blur lg:sticky lg:top-[72px]">
        <div className="container grid gap-2 py-3 sm:grid-cols-2 lg:grid-cols-[1fr_repeat(4,minmax(0,11rem))]">
          <div className="relative sm:col-span-2 lg:col-span-1">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search bills by title or number" className="pl-10" aria-label="Search legislation" type="search" />
          </div>
          <Select aria-label="Category" value={params.get("category") ?? ""} onChange={(e) => set("category", e.target.value)}>
            <option value="">All categories</option>
            {meta.data?.legislation_categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </Select>
          <Select aria-label="Year" value={params.get("year") ?? ""} onChange={(e) => set("year", e.target.value)}>
            <option value="">Any year</option>
            {meta.data?.legislation_years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </Select>
          <Select aria-label="Legislative stage" value={params.get("stage") ?? ""} onChange={(e) => set("stage", e.target.value)}>
            <option value="">Any stage</option>
            {(Object.keys(LEGISLATIVE_STAGES) as LegislativeStage[]).map((k) => (
              <option key={k} value={k}>{LEGISLATIVE_STAGES[k].label}</option>
            ))}
          </Select>
          <Select aria-label="Verification" value={params.get("verification") ?? ""} onChange={(e) => set("verification", e.target.value)}>
            <option value="">Any verification</option>
            {Object.entries(VERIFICATION).map(([k, v]) => (
              <option key={k} value={k}>{v.label}</option>
            ))}
          </Select>
        </div>
      </div>

      <section className="container py-8">
        <div className="mb-6 rounded-2xl bg-surface p-4 text-sm text-slate-600 ring-1 ring-border">
          <p className="flex items-center gap-2 font-semibold text-navy">
            <Gavel className="size-4 text-green-600" /> How to read a stage
          </p>
          <ul className="mt-2 grid gap-1.5 sm:grid-cols-2">
            {(Object.keys(LEGISLATIVE_STAGES) as LegislativeStage[]).map((k) => (
              <li key={k} className="flex items-start gap-2">
                <StageBadge stage={k} className="shrink-0" />
                <span className="text-[13px]">{LEGISLATIVE_STAGES[k].description}</span>
              </li>
            ))}
          </ul>
        </div>
        <p className="mb-6 text-sm text-muted-foreground" aria-live="polite">
          {data ? (
            <>
              <strong className="text-navy">{data.meta.total}</strong> legislative record{data.meta.total === 1 ? "" : "s"}
              {isFetching && " · updating…"}
            </>
          ) : (
            "Loading…"
          )}
          {(active > 0 || q) && (
            <button onClick={clear} className="ml-3 inline-flex items-center gap-1 font-semibold text-green-600 hover:underline">
              <X className="size-3.5" /> Clear filters
            </button>
          )}
        </p>
        {error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : isLoading ? (
          <CardSkeleton count={6} />
        ) : !data?.data.length ? (
          <EmptyState icon={FileSearch} title="No legislative records match" description="Try removing a filter." action={<Button variant="outline" onClick={clear}>Clear all filters</Button>} />
        ) : (
          <div className={cn("grid gap-5 sm:grid-cols-2 lg:grid-cols-3", isFetching && "opacity-70")}>
            {data.data.map((r) => (
              <LegislationCard key={r.id} r={r} />
            ))}
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
