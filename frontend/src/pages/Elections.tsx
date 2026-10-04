import { useQuery } from "@tanstack/react-query";
import { CalendarDays, Vote } from "lucide-react";
import { VerificationBadge } from "@/components/shared/badges";
import { PageHeader } from "@/components/shared/PageHeader";
import { Seo } from "@/components/shared/Seo";
import { RecordTabs, SourceLine, SourceList } from "@/components/shared/SourceLine";
import { ErrorState } from "@/components/shared/states";
import { CardSkeleton } from "@/components/ui/skeleton";
import { getData } from "@/lib/api";
import type { ElectionRecord } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

export function ElectionCard({ e, compact = false }: { e: ElectionRecord; compact?: boolean }) {
  return (
    <article
      id={e.slug}
      className={cn("rounded-2xl border bg-white p-5 shadow-card sm:p-6", e.is_current ? "border-green-500 ring-1 ring-green-500" : "border-border")}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="grid size-10 place-items-center rounded-xl bg-navy text-sm font-extrabold text-white">{e.year}</span>
        <h3 className="text-lg font-bold leading-snug">{e.title}</h3>
        {e.is_current && <span className="rounded-full bg-green-600 px-2.5 py-0.5 text-xs font-semibold text-white">Current</span>}
        <VerificationBadge status={e.verification_status} className="sm:ml-auto" />
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["Candidate", e.candidate],
          ["Party", e.party],
          ["Constituency", e.constituency],
          ["Outcome", e.outcome],
        ].map(([k, v]) => (
          <div key={k}>
            <dt className="text-xs font-semibold uppercase tracking-wider text-slate-500">{k}</dt>
            <dd className="mt-0.5 font-semibold text-navy">{v || "Information pending verification."}</dd>
          </div>
        ))}
      </dl>
      {(e.election_date || e.votes) && (
        <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-600">
          {e.election_date && (
            <span className="flex items-center gap-1.5">
              <CalendarDays className="size-4 text-green-600" /> Election date: {formatDate(e.election_date, { day: "numeric", month: "long", year: "numeric" })}
            </span>
          )}
          {e.votes != null && (
            <span className="flex items-center gap-1.5">
              <Vote className="size-4 text-green-600" /> {e.votes.toLocaleString("en-NG")} votes{e.votes_note ? ` — ${e.votes_note}` : ""}
            </span>
          )}
        </div>
      )}
      {!compact && (
        <>
          <p className="mt-4 text-slate-600">{e.summary}</p>
          {e.verification_note && <p className="mt-2 text-sm italic text-slate-500">{e.verification_note}</p>}
          <div className="mt-5 grid gap-5 border-t border-border pt-4 lg:grid-cols-2">
            <SourceLine source={e.sources[0]?.name} sourceUrl={e.sources[0]?.url} verification={e.verification_status} updated={e.updated_at} />
            <div>
              <p className="mb-2 text-sm font-semibold text-navy">All sources</p>
              <SourceList sources={e.sources} />
            </div>
          </div>
        </>
      )}
    </article>
  );
}

export default function Elections() {
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["elections"], queryFn: () => getData<ElectionRecord[]>("/api/elections") });
  return (
    <>
      <Seo title="Elections" description="Senator Philip Tanimu Aduda's FCT senatorial election records for 2019, 2023 and 2027, from INEC and other sources." />
      <PageHeader
        eyebrow="Our Record"
        title="Election records"
        description="FCT senatorial election records, with INEC as the authoritative source for candidacy and results."
        crumbs={[{ to: "/", label: "Home" }, { to: "/our-record", label: "Our Record" }, { label: "Elections" }]}
      >
        <RecordTabs />
      </PageHeader>
      <section className="container max-w-5xl space-y-6 py-10">
        {error ? <ErrorState error={error} onRetry={() => refetch()} /> : isLoading ? <CardSkeleton count={3} /> : data?.map((e) => <ElectionCard key={e.id} e={e} />)}
      </section>
    </>
  );
}
