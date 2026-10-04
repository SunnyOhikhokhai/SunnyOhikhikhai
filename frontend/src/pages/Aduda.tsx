import { useQuery } from "@tanstack/react-query";
import { ArrowRight, BookOpenCheck, CalendarDays, ExternalLink, FileText, Gavel, Newspaper, Vote } from "lucide-react";
import { Link } from "react-router-dom";
import { Portrait } from "@/components/brand/Portrait";
import { VerificationBadge } from "@/components/shared/badges";
import { Markdown } from "@/components/shared/Markdown";
import { Seo } from "@/components/shared/Seo";
import { ShareButton } from "@/components/shared/Share";
import { ErrorState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { getData } from "@/lib/api";
import type { ElectionRecord, PrincipalProfile } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { ElectionCard } from "./Elections";

export function useProfile() {
  return useQuery({ queryKey: ["profile"], queryFn: () => getData<PrincipalProfile>("/api/profile"), staleTime: 5 * 60_000 });
}

const isHttp = (u?: string | null) => !!u && /^https?:\/\//.test(u);

function SourceLink({ name, url, className }: { name?: string | null; url?: string | null; className?: string }) {
  if (!name) return <span className={className}>Information pending verification.</span>;
  return isHttp(url) ? (
    <a href={url!} target="_blank" rel="noopener noreferrer" className={`inline-flex items-center gap-1 font-medium text-green-700 hover:underline ${className ?? ""}`}>
      {name} <ExternalLink className="size-3 shrink-0" aria-hidden />
    </a>
  ) : (
    <span className={className}>{name}</span>
  );
}

/** Self-reported figures, always shown with their label and source. */
export function SelfReportedMetrics({ p, tone = "light" }: { p: Pick<PrincipalProfile, "metrics" | "metrics_note" | "metrics_source_url">; tone?: "light" | "dark" }) {
  if (!p.metrics?.length) return null;
  const dark = tone === "dark";
  return (
    <div>
      <dl className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {p.metrics.map((m) => (
          <div key={m.label} className={dark ? "rounded-2xl bg-white/5 p-4 ring-1 ring-white/10" : "rounded-2xl bg-white p-4 shadow-card ring-1 ring-border"}>
            <dd className={`font-display text-3xl font-extrabold ${dark ? "text-white" : "text-navy"}`}>{m.value}</dd>
            <dt className={`mt-1 text-sm ${dark ? "text-navy-100" : "text-slate-600"}`}>{m.label}</dt>
          </div>
        ))}
      </dl>
      <p className={`mt-3 flex flex-wrap items-center gap-2 text-xs ${dark ? "text-navy-100" : "text-slate-500"}`}>
        <VerificationBadge status="self_reported" />
        <span>
          {p.metrics_note}{" "}
          {isHttp(p.metrics_source_url) && (
            <a href={p.metrics_source_url!} target="_blank" rel="noopener noreferrer" className="font-semibold underline">
              Source
            </a>
          )}{" "}
          Not independently audited.
        </span>
      </p>
    </div>
  );
}

export default function Aduda() {
  const { user } = useAuth();
  const { data: p, isLoading, error, refetch } = useProfile();
  const elections = useQuery({ queryKey: ["elections"], queryFn: () => getData<ElectionRecord[]>("/api/elections") });
  const current = elections.data?.find((e) => e.is_current);
  if (error) return <div className="container py-16"><ErrorState error={error} onRetry={() => refetch()} /></div>;

  return (
    <>
      <Seo
        title={p?.name ?? "Senator Philip Tanimu Aduda"}
        description={p?.summary?.slice(0, 160) ?? "Senator Philip Tanimu Aduda — sourced profile, public service and milestones."}
        image={p?.photo_url}
        jsonLd={p ? { "@context": "https://schema.org", "@type": "Person", name: "Philip Tanimu Aduda", honorificPrefix: "Senator", jobTitle: p.title || undefined, image: p.photo_url || undefined } : undefined}
      />
      <section className="relative isolate overflow-hidden bg-navy text-white">
        <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_70%_60%_at_90%_0%,rgba(7,148,71,0.35),transparent_60%)]" />
        <div className="container grid items-center gap-10 py-12 sm:py-16 lg:grid-cols-[1.3fr_1fr] lg:py-20">
          <div className="order-2 min-w-0 lg:order-1">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-green-300">Profile</p>
            {isLoading || !p ? (
              <Skeleton className="mt-4 h-14 w-3/4 bg-white/10" />
            ) : (
              <>
                <h1 className="mt-3 text-4xl font-extrabold text-white sm:text-5xl">{p.name}</h1>
                {p.badges.length > 0 ? (
                  <ul className="mt-5 flex flex-col gap-2">
                    {p.badges.map((b) => (
                      <li key={b.label} className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full bg-white/10 px-3.5 py-1.5 text-sm font-semibold text-white ring-1 ring-white/20">{b.label}</span>
                        <VerificationBadge status={b.verification} className="bg-white" />
                        <SourceLink name={b.source_name} url={b.source_url} className="text-xs !text-green-200" />
                      </li>
                    ))}
                  </ul>
                ) : (
                  <>
                    {p.title && <p className="mt-3 text-lg font-semibold text-green-200">{p.title}</p>}
                    {p.tagline && <p className="mt-2 text-lg text-white">{p.tagline}</p>}
                  </>
                )}
                <p className="mt-6 max-w-2xl text-base leading-relaxed text-navy-100 sm:text-lg">{p.summary}</p>
              </>
            )}
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button asChild size="lg">
                <Link to={user ? "/community" : "/join"}>
                  {user ? "Join the conversation" : "Join NIPAM"} <ArrowRight />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline-light">
                <Link to="/our-record">See the public record</Link>
              </Button>
            </div>
          </div>
          <figure className="order-1 mx-auto w-full max-w-sm lg:order-2">
            <div className="overflow-hidden rounded-3xl shadow-lift ring-4 ring-white/10">
              <Portrait src={p?.photo_url} alt={p?.photo_alt} className="aspect-[4/5] w-full" />
            </div>
            {p && (
              <figcaption className="mt-3 text-center text-xs text-navy-100">
                {p.photo_url ? (
                  <>
                    {p.photo_caption ?? "Official portrait"}
                    {p.photo_source_name && (
                      <>
                        {" · Source: "}
                        <SourceLink name={p.photo_source_name} url={p.photo_source_url} className="!text-green-200" />
                      </>
                    )}
                  </>
                ) : (
                  <>
                    The official portrait from{" "}
                    <SourceLink name={p.photo_source_name ?? "his official website"} url={p.photo_source_url} className="!text-green-200" /> will appear
                    here once the image has been obtained with permission.
                  </>
                )}
              </figcaption>
            )}
          </figure>
        </div>
      </section>

      {p && p.facts.length > 0 && (
        <section className="container py-12" aria-labelledby="facts-heading">
          <h2 id="facts-heading" className="text-2xl font-extrabold">At a glance</h2>
          <p className="mt-1 text-sm text-muted-foreground">Every fact shows its source and verification status. Where sources differ, both are shown.</p>
          <dl className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {p.facts.map((f, i) => (
              <div key={i} className="flex flex-col gap-1.5 rounded-2xl border border-border bg-white p-4">
                <dt className="text-xs font-semibold uppercase tracking-wider text-slate-500">{f.label}</dt>
                <dd className="font-semibold text-navy">{f.value}</dd>
                {f.note && <dd className="text-[13px] text-slate-500">{f.note}</dd>}
                <dd className="mt-auto flex flex-wrap items-center gap-2 pt-1 text-xs text-slate-500">
                  <VerificationBadge status={f.verification} />
                  <SourceLink name={f.source_name} url={f.source_url} />
                </dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      {current && (
        <section className="container pb-4" aria-labelledby="election-heading">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
            <h2 id="election-heading" className="text-2xl font-extrabold">2027 election</h2>
            <Link to="/elections" className="text-sm font-semibold text-green-600 hover:underline">All election records →</Link>
          </div>
          <ElectionCard e={current} />
        </section>
      )}

      {p && p.metrics.length > 0 && (
        <section className="container py-10" aria-labelledby="metrics-heading">
          <h2 id="metrics-heading" className="mb-4 text-2xl font-extrabold">Figures from his official platform</h2>
          <SelfReportedMetrics p={p} />
        </section>
      )}

      <div className="container grid gap-12 py-12 lg:grid-cols-[1.5fr_1fr]">
        <article className="min-w-0">
          {p ? <Markdown>{p.biography}</Markdown> : <Skeleton className="h-64" />}
          <div className="mt-8 flex flex-wrap items-center gap-3 border-t border-border pt-6">
            {p && <ShareButton title={p.name} text={p.summary} />}
            {p && <p className="text-xs text-muted-foreground">Last updated {formatDate(p.updated_at, { day: "numeric", month: "long", year: "numeric" })}</p>}
          </div>
        </article>
        <aside className="space-y-5">
          <div className="rounded-2xl bg-surface p-6 ring-1 ring-border">
            <h2 className="text-lg font-extrabold">The public record</h2>
            <ul className="mt-4 space-y-2">
              {[
                ["/our-record", "Constituency projects", FileText],
                ["/legislation", "Legislative record", Gavel],
                ["/elections", "Election records", Vote],
                ["/news", "News and explainers", Newspaper],
                ["/events", "Upcoming events", CalendarDays],
                ["/about", "About NIPAM", BookOpenCheck],
              ].map(([to, label, Icon]) => {
                const I = Icon as typeof FileText;
                return (
                  <li key={to as string}>
                    <Link to={to as string} className="flex items-center gap-3 rounded-xl bg-white px-4 py-3 text-sm font-semibold text-navy shadow-card transition hover:text-green-600">
                      <I className="size-4 text-green-600" /> {label as string}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
          {p && p.links.length > 0 && (
            <div className="rounded-2xl border border-border p-6">
              <h2 className="text-lg font-extrabold">Official links</h2>
              <ul className="mt-3 space-y-2">
                {p.links.map((l) => (
                  <li key={l.url}>
                    <a href={l.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 text-sm font-semibold text-green-600 hover:underline">
                      {l.label} <ExternalLink className="size-3.5" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </aside>
      </div>

      {p && p.timeline.length > 0 && (
        <section className="section bg-surface" aria-labelledby="timeline-heading">
          <div className="container max-w-4xl">
            <p className="eyebrow mb-3">Milestones</p>
            <h2 id="timeline-heading" className="text-3xl font-extrabold">Political timeline</h2>
            <ol className="relative mt-10 space-y-8 border-l-2 border-green-500/40 pl-8">
              {p.timeline.map((t, i) => (
                <li key={i} className="relative">
                  <span className="absolute -left-[42px] top-1 flex size-5 items-center justify-center rounded-full bg-green-600 ring-4 ring-surface" aria-hidden />
                  <p className="font-display text-sm font-extrabold uppercase tracking-wider text-green-600">{t.year}</p>
                  <h3 className="mt-1 text-lg font-bold">{t.title}</h3>
                  {t.description && <p className="mt-1 text-muted-foreground">{t.description}</p>}
                  <p className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    {t.verification && <VerificationBadge status={t.verification} />}
                    <span>
                      Source:{" "}
                      {t.source_name ? <SourceLink name={t.source_name} url={t.source} /> : isHttp(t.source) ? <SourceLink name={t.source} url={t.source} /> : t.source || "Information pending verification."}
                    </span>
                  </p>
                </li>
              ))}
            </ol>
          </div>
        </section>
      )}

      {p && p.gallery.length > 0 && (
        <section className="section" aria-labelledby="gallery-heading">
          <div className="container">
            <h2 id="gallery-heading" className="mb-8 text-3xl font-extrabold">Gallery</h2>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
              {p.gallery.map((g, i) => (
                <figure key={i} className="overflow-hidden rounded-2xl border border-border bg-white shadow-card">
                  <img src={g.url} alt={g.alt} loading="lazy" className="aspect-[4/3] w-full object-cover" />
                  <figcaption className="space-y-0.5 p-3 text-sm text-slate-600">
                    {g.caption && <p>{g.caption}</p>}
                    {g.source_name && (
                      <p className="text-xs text-slate-500">
                        Source: <SourceLink name={g.source_name} url={g.source_url} />
                        {g.date && <> · {g.date}</>}
                      </p>
                    )}
                  </figcaption>
                </figure>
              ))}
            </div>
          </div>
        </section>
      )}
    </>
  );
}
