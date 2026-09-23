import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  BadgeCheck,
  BookOpenCheck,
  FileSearch,
  Handshake,
  Megaphone,
  MessageSquare,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";
import { SkylineArt } from "@/components/brand/Artwork";
import { CouncilCard, DiscussionRow, EventCard, NewsCard, RecordCard } from "@/components/shared/cards";
import { FeaturedCarousel } from "@/components/shared/FeaturedCarousel";
import { SectionHeading } from "@/components/shared/PageHeader";
import { Seo } from "@/components/shared/Seo";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { CardSkeleton, Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { getData } from "@/lib/api";
import type { Announcement, Council, DiscussionItem, EventItem, NewsCard as NewsCardT, RecordCard as RecordCardT } from "@/lib/types";

interface HomeData {
  featured: RecordCardT[];
  councils: Council[];
  news: NewsCardT[];
  events: EventItem[];
  discussions: DiscussionItem[];
  announcements: Announcement[];
  stats: { members: number; records: number; councils: number };
}

export const PILLARS = [
  {
    icon: Users,
    title: "Community",
    text: "Connecting members and residents across all six Area Councils of the FCT, whatever their background.",
  },
  {
    icon: BookOpenCheck,
    title: "Information",
    text: "Providing accessible, factual information and public records — each clearly labelled with its source and status.",
  },
  {
    icon: Handshake,
    title: "Participation",
    text: "Creating opportunities for constructive community engagement through events, discussions and feedback.",
  },
];

function Hero({ stats }: { stats?: HomeData["stats"] }) {
  const { user } = useAuth();
  return (
    <section className="relative isolate overflow-hidden bg-navy text-white">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_80%_60%_at_85%_10%,rgba(7,148,71,0.35),transparent_60%),radial-gradient(ellipse_60%_50%_at_0%_100%,rgba(31,90,142,0.6),transparent_60%)]" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 -z-10 opacity-90">
        <SkylineArt className="h-40 w-full sm:h-56 lg:h-64" />
      </div>
      <div className="container pb-44 pt-14 sm:pb-60 sm:pt-20 lg:pb-64 lg:pt-24">
        <div className="max-w-3xl animate-fade-up">
          <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3.5 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-green-200 ring-1 ring-white/15 backdrop-blur">
            <span className="size-1.5 rounded-full bg-green-400" /> Federal Capital Territory · Nigeria
          </p>
          <h1 className="mt-6 font-display text-6xl font-extrabold tracking-[0.04em] text-white sm:text-7xl lg:text-8xl">
            NIP<span className="text-green-400">A</span>M
          </h1>
          <p className="mt-3 font-display text-xl font-semibold text-navy-100 sm:text-2xl">Non-Indigenes for Philip Aduda Movement</p>
          <p className="mt-6 max-w-2xl text-base leading-relaxed text-navy-100 sm:text-lg">
            A digital community connecting residents, sharing information, documenting public records and facilitating constructive civic
            engagement across the Federal Capital Territory.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Button asChild size="lg">
              <Link to={user ? "/dashboard" : "/join"}>
                {user ? "Go to my dashboard" : "Join NIPAM"} <ArrowRight />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline-light">
              <a href="#explore">Explore NIPAM</a>
            </Button>
          </div>
          <dl className="mt-12 grid max-w-lg grid-cols-3 gap-6 border-t border-white/15 pt-6">
            {[
              ["Area Councils", stats?.councils ?? 6],
              ["Public records", stats?.records],
              ["Members", stats?.members],
            ].map(([label, value]) => (
              <div key={label as string}>
                <dt className="text-xs font-medium uppercase tracking-wider text-navy-200">{label}</dt>
                <dd className="mt-1 font-display text-3xl font-extrabold text-white">
                  {value === undefined ? <Skeleton className="h-8 w-12 bg-white/10" /> : Number(value).toLocaleString("en-NG")}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  const { user } = useAuth();
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["home"], queryFn: () => getData<HomeData>("/api/home") });

  return (
    <>
      <Seo
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "Organization",
          name: "NIPAM",
          alternateName: "Non-Indigenes for Philip Aduda Movement",
          url: window.location.origin,
          logo: `${window.location.origin}/icons/icon-512.png`,
          areaServed: "Federal Capital Territory, Nigeria",
        }}
      />
      <Hero stats={data?.stats} />

      {/* Featured rotating records */}
      <section id="explore" className="relative -mt-24 scroll-mt-24 pb-16 sm:-mt-32">
        <div className="container">
          {data?.announcements?.[0] && (
            <Link
              to={data.announcements[0].link_url ?? "/news"}
              className="mb-5 flex items-center gap-3 rounded-2xl bg-white/95 p-3 pr-4 text-sm shadow-card ring-1 ring-border backdrop-blur transition hover:ring-green-500"
            >
              <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-green-600 text-white">
                <Megaphone className="size-4" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="font-semibold text-navy">{data.announcements[0].title}</span>
                <span className="hidden text-muted-foreground sm:inline"> — {data.announcements[0].body}</span>
              </span>
              <ArrowRight className="size-4 shrink-0 text-green-600" />
            </Link>
          )}
          {isLoading ? (
            <Skeleton className="h-[30rem] rounded-3xl lg:h-[26rem]" />
          ) : error ? (
            <ErrorState error={error} onRetry={() => refetch()} className="bg-white" />
          ) : data?.featured.length ? (
            <FeaturedCarousel items={data.featured} />
          ) : (
            <EmptyState title="Featured records coming soon" description="Verified records will appear here as they are published." className="bg-white" />
          )}
        </div>
      </section>

      {/* About */}
      <section className="section bg-white" aria-labelledby="about-heading">
        <div className="container">
          <div className="grid gap-12 lg:grid-cols-[1fr_1.2fr] lg:gap-16">
            <div>
              <p className="eyebrow mb-3">About NIPAM</p>
              <h2 id="about-heading" className="text-3xl font-extrabold sm:text-4xl">
                A community platform for residents of the FCT
              </h2>
              <p className="mt-5 text-lg leading-relaxed text-muted-foreground">
                NIPAM brings together residents and voluntary members across the Federal Capital Territory. We share accessible information,
                document public records with their sources, and create space for respectful civic conversation.
              </p>
              <ul className="mt-6 space-y-3 text-[15px] text-slate-700">
                {[
                  "Membership is voluntary and free — you choose how to take part.",
                  "Every record shows its verification status and source.",
                  "You control which communications you receive.",
                ].map((t) => (
                  <li key={t} className="flex gap-3">
                    <BadgeCheck className="mt-0.5 size-5 shrink-0 text-green-600" /> {t}
                  </li>
                ))}
              </ul>
              <Button asChild variant="outline" className="mt-8">
                <Link to="/about">
                  Learn more about NIPAM <ArrowRight />
                </Link>
              </Button>
            </div>
            <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
              {PILLARS.map(({ icon: Icon, title, text }, i) => (
                <div
                  key={title}
                  className={
                    i === 1
                      ? "rounded-2xl bg-navy p-6 text-white shadow-lift"
                      : "rounded-2xl border border-border bg-surface p-6 transition hover:border-navy-200 hover:bg-white hover:shadow-card"
                  }
                >
                  <div className={i === 1 ? "flex size-12 items-center justify-center rounded-xl bg-green-600" : "flex size-12 items-center justify-center rounded-xl bg-navy text-white"}>
                    <Icon className="size-6" />
                  </div>
                  <h3 className={i === 1 ? "mt-5 text-lg font-extrabold uppercase tracking-[0.1em] text-white" : "mt-5 text-lg font-extrabold uppercase tracking-[0.1em]"}>
                    {title}
                  </h3>
                  <p className={i === 1 ? "mt-2 text-sm leading-relaxed text-navy-100" : "mt-2 text-sm leading-relaxed text-muted-foreground"}>{text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Area Councils */}
      <section className="section bg-surface" aria-labelledby="councils-heading">
        <div className="container">
          <SectionHeading
            eyebrow="FCT Area Councils"
            title={<span id="councils-heading">Six councils, one community</span>}
            description="Explore updates, events, public information and records for each of the six Area Councils of the Federal Capital Territory."
            action={
              <Button asChild variant="outline">
                <Link to="/area-councils">
                  View map <ArrowRight />
                </Link>
              </Button>
            }
          />
          {isLoading ? (
            <CardSkeleton count={6} />
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {data?.councils.map((c, i) => <CouncilCard key={c.slug} council={c} index={i} />)}
            </div>
          )}
        </div>
      </section>

      {/* Public record highlights */}
      <section className="section bg-white" aria-labelledby="record-heading">
        <div className="container">
          <SectionHeading
            eyebrow="Our Record"
            title={<span id="record-heading">Evidence-based public records</span>}
            description="A searchable library of documented projects and public activities. Each entry carries a verification status and its sources."
            action={
              <Button asChild variant="outline">
                <Link to="/our-record">
                  Browse all records <ArrowRight />
                </Link>
              </Button>
            }
          />
          <div className="mb-10 grid gap-4 sm:grid-cols-3">
            {[
              [FileSearch, "Source-cited", "Records reference who published the information and when."],
              [ShieldCheck, "Clearly labelled", "Verified, pending review, unverified or disputed — always visible."],
              [Sparkles, "Sample content marked", "Demonstration entries are labelled until verified data is added."],
            ].map(([Icon, t, d]) => {
              const I = Icon as typeof FileSearch;
              return (
                <div key={t as string} className="flex gap-3 rounded-2xl border border-border p-4">
                  <I className="size-5 shrink-0 text-green-600" />
                  <div>
                    <p className="text-sm font-bold text-navy">{t as string}</p>
                    <p className="text-[13px] text-muted-foreground">{d as string}</p>
                  </div>
                </div>
              );
            })}
          </div>
          {isLoading ? (
            <CardSkeleton />
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {data?.featured.slice(0, 3).map((r) => <RecordCard key={r.id} record={r} />)}
            </div>
          )}
        </div>
      </section>

      {/* News + Events */}
      <section className="section bg-surface" aria-labelledby="news-heading">
        <div className="container grid gap-14 lg:grid-cols-[1.5fr_1fr]">
          <div>
            <SectionHeading
              eyebrow="Latest News"
              title={<span id="news-heading">Updates from across the FCT</span>}
              action={
                <Link to="/news" className="inline-flex items-center gap-1.5 text-sm font-semibold text-green-600 hover:gap-2.5 hover:text-green-700">
                  All news <ArrowRight className="size-4" />
                </Link>
              }
              className="mb-8"
            />
            {isLoading ? (
              <CardSkeleton count={2} className="lg:grid-cols-2" />
            ) : data?.news.length ? (
              <div className="grid gap-6 sm:grid-cols-2">
                {data.news.slice(0, 2).map((n) => <NewsCard key={n.id} item={n} />)}
              </div>
            ) : (
              <EmptyState title="No news yet" />
            )}
          </div>
          <div>
            <SectionHeading
              eyebrow="Upcoming Events"
              title="Get involved"
              action={
                <Link to="/events" className="inline-flex items-center gap-1.5 text-sm font-semibold text-green-600 hover:gap-2.5 hover:text-green-700">
                  All events <ArrowRight className="size-4" />
                </Link>
              }
              className="mb-8"
            />
            {isLoading ? (
              <div className="space-y-4">
                {[0, 1, 2].map((i) => (
                  <Skeleton key={i} className="h-28" />
                ))}
              </div>
            ) : data?.events.length ? (
              <div className="space-y-4">
                {data.events.map((e) => <EventCard key={e.id} event={e} />)}
              </div>
            ) : (
              <EmptyState title="No upcoming events" description="New events will be announced here." />
            )}
          </div>
        </div>
      </section>

      {/* Community */}
      <section className="section bg-white" aria-labelledby="community-heading">
        <div className="container grid gap-12 lg:grid-cols-[1fr_1.4fr] lg:items-start">
          <div className="lg:sticky lg:top-28">
            <p className="eyebrow mb-3">Community</p>
            <h2 id="community-heading" className="text-3xl font-extrabold sm:text-4xl">
              Constructive conversations, moderated with care
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
              Share ideas, ask questions and connect with residents in your Area Council. Our community guidelines keep discussions respectful and safe.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Button asChild>
                <Link to="/community">
                  <MessageSquare /> Visit the community
                </Link>
              </Button>
              <Button asChild variant="ghost">
                <Link to="/community-guidelines">Read the guidelines</Link>
              </Button>
            </div>
          </div>
          <div className="space-y-4">
            {isLoading
              ? [0, 1, 2].map((i) => <Skeleton key={i} className="h-28" />)
              : data?.discussions.map((d) => <DiscussionRow key={d.id} d={d} />)}
          </div>
        </div>
      </section>

      {/* Join */}
      {!user && (
        <section className="pb-20 pt-4" aria-labelledby="join-heading">
          <div className="container">
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-navy-700 via-navy-800 to-navy-900 px-6 py-14 text-center shadow-lift sm:px-12 sm:py-16">
              <div className="pointer-events-none absolute -left-20 -top-20 size-72 rounded-full bg-green-500/20 blur-3xl" />
              <div className="pointer-events-none absolute -bottom-24 -right-10 size-72 rounded-full border-[30px] border-white/5" />
              <p className="eyebrow text-green-300">Join the movement</p>
              <h2 id="join-heading" className="mx-auto mt-3 max-w-2xl text-3xl font-extrabold text-white sm:text-4xl">
                Be part of a connected, informed FCT community
              </h2>
              <p className="mx-auto mt-4 max-w-xl text-navy-100">
                Create your free account in minutes. Choose your Area Council, follow updates and events, and take part in the conversation.
              </p>
              <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
                <Button asChild size="lg">
                  <Link to="/join">
                    Join NIPAM <ArrowRight />
                  </Link>
                </Button>
                <Button asChild size="lg" variant="outline-light">
                  <Link to="/login">I already have an account</Link>
                </Button>
              </div>
            </div>
          </div>
        </section>
      )}
    </>
  );
}
