import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { StageBadge, VerificationBadge } from "@/components/shared/badges";
import { Seo } from "@/components/shared/Seo";
import { ShareButton } from "@/components/shared/Share";
import { SourceLine, SourceList } from "@/components/shared/SourceLine";
import { ErrorState } from "@/components/shared/states";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, getData } from "@/lib/api";
import { LEGISLATIVE_STAGES, PENDING_INFO, VERIFICATION } from "@/lib/constants";
import type { LegislationRecord } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { LegislationCard } from "./Legislation";
import NotFound from "./NotFound";

export default function LegislationDetail() {
  const { slug = "" } = useParams();
  const { data: r, isLoading, error, refetch } = useQuery({
    queryKey: ["legislation", slug],
    queryFn: () => getData<LegislationRecord>(`/api/legislation/${slug}`),
  });
  if (error instanceof ApiError && error.status === 404) return <NotFound />;
  if (error) return <div className="container py-16"><ErrorState error={error} onRetry={() => refetch()} /></div>;
  if (isLoading || !r)
    return (
      <div className="container max-w-4xl space-y-6 py-12">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-12 w-3/4" />
        <Skeleton className="h-40" />
      </div>
    );
  const stage = LEGISLATIVE_STAGES[r.legislative_stage] ?? LEGISLATIVE_STAGES.pending;
  const v = VERIFICATION[r.verification_status] ?? VERIFICATION.pending;
  const facts: [string, string][] = [
    ["Bill number", r.bill_number ?? PENDING_INFO],
    ["Category", r.category],
    ["Year", r.year ? String(r.year) : PENDING_INFO],
    ["Sponsor", r.sponsor || PENDING_INFO],
    ["Legislative stage", stage.label],
    ["Status in source", r.official_status ?? PENDING_INFO],
  ];

  return (
    <article>
      <Seo title={r.title} description={r.description} type="article" />
      <div className="border-b border-border bg-surface">
        <div className="container max-w-4xl py-10 sm:py-14">
          <nav aria-label="Breadcrumb" className="mb-5 text-sm text-slate-500">
            <Link to="/legislation" className="font-semibold text-green-600 hover:underline">Legislation</Link>
            <span className="mx-2">/</span>
            <span>{r.category}</span>
          </nav>
          <div className="mb-4 flex flex-wrap gap-2">
            <StageBadge stage={r.legislative_stage} />
            <VerificationBadge status={r.verification_status} />
          </div>
          <h1 className="text-3xl font-extrabold leading-tight sm:text-4xl">{r.title}</h1>
          <p className="mt-4 max-w-3xl text-lg text-muted-foreground">{r.description}</p>
          <div className="mt-6 flex flex-wrap items-end justify-between gap-4 rounded-xl bg-white p-4 ring-1 ring-border">
            <SourceLine source={r.sources[0]?.name} sourceUrl={r.sources[0]?.url} verification={r.verification_status} updated={r.updated_at} />
            <ShareButton title={r.title} text={r.description} />
          </div>
        </div>
      </div>
      <div className="container grid max-w-4xl gap-10 py-10 lg:grid-cols-[1fr_280px]">
        <div className="min-w-0 space-y-8">
          <dl className="grid gap-3 sm:grid-cols-2">
            {facts.map(([k, val]) => (
              <div key={k} className="rounded-xl p-4 ring-1 ring-border">
                <dt className="text-xs font-semibold uppercase tracking-wider text-slate-500">{k}</dt>
                <dd className="mt-1 font-semibold text-navy">{val}</dd>
              </div>
            ))}
          </dl>
          <section>
            <h2 className="text-xl font-extrabold">What this stage means</h2>
            <p className="mt-2 text-slate-600">{stage.description}</p>
            {r.legislative_stage !== "assented" && (
              <p className="mt-2 text-sm text-slate-500">
                This record is not shown as law. It will only be shown as assented/enacted when an official enactment or assent record is added.
              </p>
            )}
          </section>
          <section>
            <h2 className="text-xl font-extrabold">Sources</h2>
            <SourceList sources={r.sources} className="mt-4" />
          </section>
        </div>
        <aside className="space-y-4">
          <div className="rounded-2xl bg-surface p-5 ring-1 ring-border">
            <p className="text-sm font-bold text-navy">Verification: {v.label}</p>
            <p className="mt-1.5 text-sm text-slate-600">{v.description}</p>
            {r.verification_note && <p className="mt-2 text-sm italic text-slate-600">“{r.verification_note}”</p>}
            {r.last_verified_at && <p className="mt-2 text-xs text-slate-500">Last verified {formatDate(r.last_verified_at)}</p>}
          </div>
          <p className="text-xs leading-relaxed text-slate-500">
            Have an official record for this bill? <Link to="/contact" className="font-semibold text-green-600 hover:underline">Send it to us</Link>.
          </p>
        </aside>
      </div>
      {r.related && r.related.length > 0 && (
        <section className="border-t border-border bg-surface py-12">
          <div className="container">
            <h2 className="mb-6 text-2xl font-extrabold">More {r.category.toLowerCase()} bills</h2>
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {r.related.map((x) => (
                <LegislationCard key={x.id} r={x} />
              ))}
            </div>
          </div>
        </section>
      )}
    </article>
  );
}
