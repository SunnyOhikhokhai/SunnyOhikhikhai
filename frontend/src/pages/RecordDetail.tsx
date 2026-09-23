import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CalendarDays, ExternalLink, FileDown, FileText, Info, MapPin, Tag } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { CoverArt } from "@/components/brand/Artwork";
import { DemoBadge, VerificationBadge } from "@/components/shared/badges";
import { RecordCard } from "@/components/shared/cards";
import { Markdown } from "@/components/shared/Markdown";
import { Seo } from "@/components/shared/Seo";
import { ShareButton } from "@/components/shared/Share";
import { ErrorState } from "@/components/shared/states";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, getData } from "@/lib/api";
import { VERIFICATION } from "@/lib/constants";
import type { RecordDetail as RecordDetailT } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";
import NotFound from "./NotFound";

export default function RecordDetail() {
  const { slug = "" } = useParams();
  const [img, setImg] = useState(0);
  const { data: r, isLoading, error, refetch } = useQuery({
    queryKey: ["record", slug],
    queryFn: () => getData<RecordDetailT>(`/api/projects/${slug}`),
  });
  if (error instanceof ApiError && error.status === 404) return <NotFound />;
  if (error) return <div className="container py-16"><ErrorState error={error} onRetry={() => refetch()} /></div>;
  if (isLoading || !r)
    return (
      <div className="container max-w-5xl space-y-6 py-12">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-12 w-3/4" />
        <Skeleton className="aspect-[16/8]" />
      </div>
    );

  const v = VERIFICATION[r.verification_status];
  const when = r.record_date ? formatDate(r.record_date) : r.year ? String(r.year) : null;
  const current = r.images[img];

  return (
    <article>
      <Seo
        title={r.title}
        description={r.summary}
        image={r.images[0]?.url}
        type="article"
        jsonLd={{ "@context": "https://schema.org", "@type": "Article", headline: r.title, datePublished: r.published_at, dateModified: r.updated_at, publisher: { "@type": "Organization", name: "NIPAM" } }}
      />
      <div className="border-b border-border bg-surface">
        <div className="container max-w-5xl py-10 sm:py-14">
          <nav aria-label="Breadcrumb" className="mb-5 text-sm text-slate-500">
            <Link to="/our-record" className="font-semibold text-green-600 hover:underline">Our Record</Link>
            <span className="mx-2">/</span>
            <span>{r.category.name}</span>
          </nav>
          <div className="mb-4 flex flex-wrap gap-2">
            <VerificationBadge status={r.verification_status} />
            {r.is_demo && <DemoBadge />}
          </div>
          <h1 className="text-3xl font-extrabold leading-tight sm:text-4xl lg:text-5xl">{r.title}</h1>
          <p className="mt-4 max-w-3xl text-lg text-muted-foreground">{r.summary}</p>
          <dl className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              [MapPin, "Location", r.location ?? "To be added"],
              [Tag, "Area Council", r.area_council?.name ?? "FCT-wide"],
              [CalendarDays, "Date / year", when ?? "To be added"],
              [FileText, "Category", r.category.name],
            ].map(([Icon, label, value]) => {
              const I = Icon as typeof MapPin;
              return (
                <div key={label as string} className="rounded-xl bg-white p-4 ring-1 ring-border">
                  <dt className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    <I className="size-3.5 text-green-600" /> {label as string}
                  </dt>
                  <dd className="mt-1 font-semibold text-navy">{value as string}</dd>
                </div>
              );
            })}
          </dl>
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-slate-500">Recorded on {formatDate(r.published_at)} · Last updated {formatDate(r.updated_at)}</p>
            <ShareButton title={r.title} text={r.summary} />
          </div>
        </div>
      </div>

      <div className="container grid max-w-5xl gap-10 py-10 lg:grid-cols-[1fr_300px]">
        <div className="min-w-0 space-y-8">
          <figure>
            <div className="overflow-hidden rounded-2xl border border-border">
              {current ? (
                <img src={current.url} alt={current.alt} className="aspect-[16/9] w-full object-cover" />
              ) : (
                <CoverArt seed={r.slug} icon={r.category.slug} className="aspect-[16/9] w-full" label="No photographs yet" />
              )}
            </div>
            {current && (current.caption || current.credit) && (
              <figcaption className="mt-2 text-sm text-slate-500">
                {current.caption} {current.credit && <span className="text-slate-400">· Photo: {current.credit}</span>}
              </figcaption>
            )}
            {r.images.length > 1 && (
              <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
                {r.images.map((im, i) => (
                  <button key={i} onClick={() => setImg(i)} aria-label={`Show image ${i + 1}`} aria-pressed={i === img} className={cn("size-20 shrink-0 overflow-hidden rounded-lg ring-2", i === img ? "ring-green-500" : "ring-transparent opacity-70 hover:opacity-100")}>
                    <img src={im.url} alt="" className="size-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </figure>

          <section aria-labelledby="desc">
            <h2 id="desc" className="text-2xl font-extrabold">Description</h2>
            <Markdown className="mt-2">{r.description || "_No description provided yet._"}</Markdown>
          </section>

          {r.documents.length > 0 && (
            <section aria-labelledby="docs">
              <h2 id="docs" className="text-2xl font-extrabold">Supporting documents</h2>
              <ul className="mt-4 space-y-2">
                {r.documents.map((d, i) => (
                  <li key={i}>
                    <a href={d.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 rounded-xl border border-border p-4 transition hover:border-green-500 hover:bg-green-50/40">
                      <FileDown className="size-5 text-green-600" />
                      <span className="flex-1 font-semibold text-navy">{d.title}</span>
                      <span className="text-xs uppercase text-slate-500">{d.file_type ?? "file"}</span>
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>

        <aside className="space-y-5">
          <div className={cn("rounded-2xl p-5 ring-1", r.verification_status === "verified" ? "bg-green-50 ring-green-200" : "bg-amber-50/60 ring-amber-200")}>
            <p className="flex items-center gap-2 text-sm font-bold text-navy">
              {r.verification_status === "verified" ? <Info className="size-4 text-green-600" /> : <AlertTriangle className="size-4 text-amber-600" />}
              Verification: {v.label}
            </p>
            <p className="mt-1.5 text-sm text-slate-600">{v.description}</p>
            {r.verification_note && <p className="mt-2 text-sm italic text-slate-600">“{r.verification_note}”</p>}
          </div>

          <div className="rounded-2xl border border-border p-5">
            <h2 className="text-base font-bold">Sources & references</h2>
            {r.sources.length ? (
              <ol className="mt-3 space-y-3">
                {r.sources.map((s, i) => (
                  <li key={i} className="text-sm">
                    <p className="font-semibold text-navy">
                      {s.url ? (
                        <a href={s.url} target="_blank" rel="noopener noreferrer nofollow" className="inline-flex items-start gap-1 hover:text-green-600">
                          {s.title} <ExternalLink className="mt-0.5 size-3.5 shrink-0" />
                        </a>
                      ) : (
                        s.title
                      )}
                    </p>
                    <p className="text-slate-500">
                      {s.publisher && <>Published by {s.publisher}</>}
                      {s.published_on && <> · {formatDate(s.published_on)}</>}
                    </p>
                    {s.notes && <p className="mt-0.5 text-slate-500">{s.notes}</p>}
                  </li>
                ))}
              </ol>
            ) : (
              <p className="mt-2 text-sm text-slate-500">
                No sources have been added yet. <span className="font-semibold text-amber-700">[SOURCE TO BE ADDED]</span> This record should be treated as unconfirmed.
              </p>
            )}
          </div>

          <p className="text-xs leading-relaxed text-slate-500">
            Spotted an error? <Link to="/contact" className="font-semibold text-green-600 hover:underline">Tell us</Link> — corrections are reviewed by the NIPAM team.
          </p>
        </aside>
      </div>

      {r.related && r.related.length > 0 && (
        <section className="border-t border-border bg-surface py-14">
          <div className="container">
            <h2 className="mb-8 text-2xl font-extrabold">Related records</h2>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">{r.related.map((x) => <RecordCard key={x.id} record={x} />)}</div>
          </div>
        </section>
      )}
    </article>
  );
}
