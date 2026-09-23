import { useQuery } from "@tanstack/react-query";
import { ArrowRight, BookOpenCheck, CalendarDays, ExternalLink, FileText, Newspaper, Quote } from "lucide-react";
import { Link } from "react-router-dom";
import { Portrait } from "@/components/brand/Portrait";
import { Markdown } from "@/components/shared/Markdown";
import { Seo } from "@/components/shared/Seo";
import { ShareButton } from "@/components/shared/Share";
import { ErrorState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { getData } from "@/lib/api";
import type { PrincipalProfile } from "@/lib/types";

export function useProfile() {
  return useQuery({ queryKey: ["profile"], queryFn: () => getData<PrincipalProfile>("/api/profile"), staleTime: 5 * 60_000 });
}

export default function Aduda() {
  const { user } = useAuth();
  const { data: p, isLoading, error, refetch } = useProfile();
  if (error) return <div className="container py-16"><ErrorState error={error} onRetry={() => refetch()} /></div>;

  return (
    <>
      <Seo
        title={p?.name ?? "Sen. Philip Aduda"}
        description={p?.summary?.slice(0, 160) ?? "About Sen. Philip Aduda — biography, public service and milestones."}
        image={p?.photo_url}
        jsonLd={p ? { "@context": "https://schema.org", "@type": "Person", name: p.name.replace(/^Sen\.\s*/, ""), honorificPrefix: "Senator", jobTitle: p.title || undefined, image: p.photo_url || undefined } : undefined}
      />
      <section className="relative isolate overflow-hidden bg-navy text-white">
        <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_70%_60%_at_90%_0%,rgba(7,148,71,0.35),transparent_60%)]" />
        <div className="container grid items-center gap-10 py-12 sm:py-16 lg:grid-cols-[1.3fr_1fr] lg:py-20">
          <div className="order-2 lg:order-1">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-green-300">NIPAM supports</p>
            {isLoading || !p ? (
              <Skeleton className="mt-4 h-14 w-3/4 bg-white/10" />
            ) : (
              <>
                <h1 className="mt-3 text-4xl font-extrabold text-white sm:text-5xl lg:text-6xl">{p.name}</h1>
                {p.title && <p className="mt-3 text-lg font-semibold text-green-200">{p.title}</p>}
                {p.tagline && (
                  <p className="mt-6 flex gap-3 border-l-4 border-green-500 pl-4 font-display text-xl font-semibold leading-snug text-white sm:text-2xl">
                    <Quote className="mt-1 size-5 shrink-0 text-green-400" aria-hidden />
                    {p.tagline}
                  </p>
                )}
                <p className="mt-6 max-w-2xl text-base leading-relaxed text-navy-100 sm:text-lg">{p.summary}</p>
              </>
            )}
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button asChild size="lg">
                <Link to={user ? "/community" : "/join"}>
                  {user ? "Join the conversation" : "Join the support movement"} <ArrowRight />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline-light">
                <Link to="/our-record">See his record</Link>
              </Button>
            </div>
          </div>
          <div className="order-1 mx-auto w-full max-w-sm lg:order-2">
            <div className="overflow-hidden rounded-3xl shadow-lift ring-4 ring-white/10">
              <Portrait src={p?.photo_url} alt={p?.photo_alt} className="aspect-[4/5] w-full" />
            </div>
          </div>
        </div>
      </section>

      <div className="container grid gap-12 py-12 lg:grid-cols-[1.5fr_1fr]">
        <article className="min-w-0">
          {p ? <Markdown>{p.biography}</Markdown> : <Skeleton className="h-64" />}
          <div className="mt-8 flex flex-wrap items-center gap-3 border-t border-border pt-6">
            {p && <ShareButton title={p.name} text={p.summary} />}
            <p className="text-xs text-muted-foreground">Profile information is published by NIPAM administrators from verified sources.</p>
          </div>
        </article>
        <aside className="space-y-5">
          <div className="rounded-2xl bg-surface p-6 ring-1 ring-border">
            <h2 className="text-lg font-extrabold">Follow his work</h2>
            <ul className="mt-4 space-y-2">
              {[
                ["/our-record", "Our Record — documented projects", FileText],
                ["/news", "Latest news and updates", Newspaper],
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
              <h2 className="text-lg font-extrabold">Official channels</h2>
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
            <h2 id="timeline-heading" className="text-3xl font-extrabold">Public service timeline</h2>
            <ol className="relative mt-10 space-y-8 border-l-2 border-green-500/40 pl-8">
              {p.timeline.map((t, i) => (
                <li key={i} className="relative">
                  <span className="absolute -left-[42px] top-1 flex size-5 items-center justify-center rounded-full bg-green-600 ring-4 ring-surface" aria-hidden />
                  <p className="font-display text-sm font-extrabold uppercase tracking-wider text-green-600">{t.year}</p>
                  <h3 className="mt-1 text-lg font-bold">{t.title}</h3>
                  {t.description && <p className="mt-1 text-muted-foreground">{t.description}</p>}
                  <p className="mt-2 text-xs text-slate-500">Source: {t.source || "Source to be added"}</p>
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
                  {g.caption && <figcaption className="p-3 text-sm text-slate-600">{g.caption}</figcaption>}
                </figure>
              ))}
            </div>
          </div>
        </section>
      )}
    </>
  );
}
