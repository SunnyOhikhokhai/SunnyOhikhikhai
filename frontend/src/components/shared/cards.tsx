import { ArrowRight, CalendarDays, Clock, Heart, MapPin, MessageSquare, Pin, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { CoverArt } from "@/components/brand/Artwork";
import { Badge } from "@/components/ui/badge";
import type { Council, DiscussionItem, EventItem, NewsCard as NewsCardT, RecordCard as RecordCardT } from "@/lib/types";
import { cn, formatDate, formatTime, timeAgo } from "@/lib/utils";
import { ContentLabelBadge, DemoBadge, VerificationBadge } from "./badges";

const cardBase =
  "group relative flex flex-col overflow-hidden rounded-2xl border border-border bg-white shadow-card transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lift focus-within:ring-2 focus-within:ring-green-500";

function Img({ src, alt, className }: { src: string; alt: string; className?: string }) {
  return <img src={src} alt={alt} loading="lazy" decoding="async" className={cn("size-full object-cover transition-transform duration-500 group-hover:scale-[1.03]", className)} />;
}

export function RecordCard({ record, view = "grid" }: { record: RecordCardT; view?: "grid" | "list" }) {
  const when = record.year ?? (record.record_date ? formatDate(record.record_date, { year: "numeric" }) : null);
  const media = record.image ? (
    <Img src={record.image.url} alt={record.image.alt} />
  ) : (
    <CoverArt seed={record.slug} icon={record.category.slug} label={record.category.name} className="size-full" />
  );
  if (view === "list")
    return (
      <article className={cn(cardBase, "sm:flex-row")}>
        <div className="aspect-[16/9] shrink-0 overflow-hidden sm:aspect-auto sm:w-56">{media}</div>
        <div className="flex flex-1 flex-col gap-2 p-5">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{record.category.name}</Badge>
            <VerificationBadge status={record.verification_status} />
            {record.is_demo && <DemoBadge />}
          </div>
          <h3 className="text-lg font-bold leading-snug">
            <Link to={`/our-record/${record.slug}`} className="after:absolute after:inset-0">
              {record.title}
            </Link>
          </h3>
          <p className="line-clamp-2 text-sm text-muted-foreground">{record.summary}</p>
          <div className="mt-auto flex flex-wrap gap-x-4 gap-y-1 pt-1 text-[13px] text-slate-500">
            {record.area_council && (
              <span className="flex items-center gap-1">
                <MapPin className="size-3.5" /> {record.location ?? record.area_council.name}
              </span>
            )}
            <span className="flex items-center gap-1">
              <CalendarDays className="size-3.5" /> {when ?? "Date to be added"}
            </span>
            <span>{record.source_count ? `${record.source_count} source${record.source_count > 1 ? "s" : ""}` : "No sources yet"}</span>
          </div>
        </div>
      </article>
    );
  return (
    <article className={cardBase}>
      <div className="relative aspect-[16/10] overflow-hidden">
        {media}
        <div className="absolute left-3 top-3 flex gap-1.5">
          {record.is_demo && <DemoBadge className="bg-white/95" />}
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-2.5 p-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-green-600">{record.category.name}</span>
          <VerificationBadge status={record.verification_status} className="ml-auto" />
        </div>
        <h3 className="text-lg font-bold leading-snug">
          <Link to={`/our-record/${record.slug}`} className="after:absolute after:inset-0">
            {record.title}
          </Link>
        </h3>
        <p className="line-clamp-2 text-sm text-muted-foreground">{record.summary}</p>
        <div className="mt-auto flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-border pt-3 text-[13px] text-slate-500">
          <span className="flex items-center gap-1">
            <MapPin className="size-3.5" /> {record.area_council?.short_name ?? "FCT"}
          </span>
          <span className="flex items-center gap-1">
            <CalendarDays className="size-3.5" /> {when ?? "Date TBA"}
          </span>
        </div>
      </div>
    </article>
  );
}

export function NewsCard({ item, compact }: { item: NewsCardT; compact?: boolean }) {
  return (
    <article className={cardBase}>
      <div className={cn("relative overflow-hidden", compact ? "aspect-[16/9]" : "aspect-[16/10]")}>
        {item.image_url ? (
          <Img src={item.image_url} alt={item.image_alt ?? ""} />
        ) : (
          <CoverArt seed={item.slug} icon="news" label={item.category.name} className="size-full" />
        )}
      </div>
      <div className="flex flex-1 flex-col gap-2.5 p-5">
        <div className="flex flex-wrap items-center gap-2">
          <ContentLabelBadge label={item.content_label} />
          {item.area_council && <Badge variant="outline">{item.area_council.short_name}</Badge>}
          {item.is_demo && <DemoBadge />}
        </div>
        <h3 className="text-lg font-bold leading-snug">
          <Link to={`/news/${item.slug}`} className="after:absolute after:inset-0">
            {item.title}
          </Link>
        </h3>
        {!compact && <p className="line-clamp-2 text-sm text-muted-foreground">{item.excerpt}</p>}
        <p className="mt-auto pt-1 text-[13px] text-slate-500">
          {item.category.name} · <time dateTime={item.published_at ?? undefined}>{formatDate(item.published_at)}</time>
        </p>
      </div>
    </article>
  );
}

export function DateBlock({ iso, className }: { iso: string; className?: string }) {
  return (
    <div className={cn("flex w-16 shrink-0 flex-col items-center rounded-xl bg-navy py-2 text-white shadow-card", className)}>
      <span className="text-[11px] font-semibold uppercase tracking-wider text-green-300">{formatDate(iso, { month: "short" })}</span>
      <span className="font-display text-2xl font-extrabold leading-none">{formatDate(iso, { day: "numeric" })}</span>
      <span className="mt-0.5 text-[10px] text-navy-200">{formatDate(iso, { weekday: "short" })}</span>
    </div>
  );
}

export function EventCard({ event, className }: { event: EventItem; className?: string }) {
  const past = new Date(event.starts_at) < new Date();
  return (
    <article className={cn(cardBase, "flex-row gap-4 p-4 sm:p-5", className)}>
      <DateBlock iso={event.starts_at} />
      <div className="flex min-w-0 flex-1 flex-col gap-1.5">
        <div className="flex flex-wrap items-center gap-1.5">
          {event.status === "cancelled" && <Badge variant="danger">Cancelled</Badge>}
          {past && event.status !== "cancelled" && <Badge variant="outline">Past event</Badge>}
          {!past && event.status === "published" && event.registration_open && <Badge variant="green">Registration open</Badge>}
          {event.is_registered && <Badge variant="solid">You're registered</Badge>}
          {event.is_demo && <DemoBadge />}
        </div>
        <h3 className="text-base font-bold leading-snug sm:text-lg">
          <Link to={`/events/${event.slug}`} className="after:absolute after:inset-0">
            {event.title}
          </Link>
        </h3>
        <div className="flex flex-col gap-1 text-[13px] text-slate-500 sm:flex-row sm:flex-wrap sm:gap-x-4">
          <span className="flex items-center gap-1">
            <Clock className="size-3.5" /> {formatTime(event.starts_at)}
          </span>
          <span className="flex min-w-0 items-center gap-1">
            <MapPin className="size-3.5 shrink-0" /> <span className="truncate">{event.location}</span>
          </span>
        </div>
      </div>
    </article>
  );
}

const COUNCIL_TINT: Record<string, string> = {
  amac: "from-navy-700 to-navy-900",
  bwari: "from-navy-600 to-navy-800",
  gwagwalada: "from-green-700 to-navy-800",
  kuje: "from-navy-700 to-green-800",
  kwali: "from-navy-800 to-navy-950",
  abaji: "from-green-800 to-navy-900",
};

export function CouncilCard({ council, index = 0 }: { council: Council; index?: number }) {
  return (
    <article className={cn(cardBase, "min-h-[18rem]")}>
      <div className={cn("relative h-28 overflow-hidden bg-gradient-to-br", COUNCIL_TINT[council.slug] ?? "from-navy-700 to-navy-900")}>
        {council.image_url && <img src={council.image_url} alt="" className="absolute inset-0 size-full object-cover opacity-40" loading="lazy" />}
        <div className="absolute -bottom-10 -right-6 font-display text-[6.5rem] font-extrabold leading-none text-white/[0.07]">{String(index + 1).padStart(2, "0")}</div>
        <div className="absolute bottom-4 left-5">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-green-300">Area Council</p>
          <h3 className="font-display text-2xl font-extrabold text-white">{council.short_name}</h3>
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-3 p-5">
        <p className="text-sm font-semibold text-navy">{council.name}</p>
        <p className="line-clamp-3 text-sm text-muted-foreground">{council.summary}</p>
        <div className="mt-auto space-y-3 border-t border-border pt-3">
          <div className="flex items-center justify-between text-[13px] text-slate-500">
            <span className="flex items-center gap-1.5">
              <Users className="size-4 text-green-600" />
              {council.member_count ?? 0} member{council.member_count === 1 ? "" : "s"}
            </span>
          </div>
          {council.latest_update ? (
            <p className="line-clamp-1 text-[13px] text-slate-600">
              <span className="font-semibold text-navy">Latest:</span> {council.latest_update.title}
            </p>
          ) : (
            <p className="text-[13px] text-slate-500">No updates yet</p>
          )}
          <Link
            to={`/area-councils/${council.slug}`}
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-green-600 after:absolute after:inset-0 group-hover:gap-2.5"
          >
            Explore {council.short_name} <ArrowRight className="size-4 transition-all" />
          </Link>
        </div>
      </div>
    </article>
  );
}

export function DiscussionRow({ d }: { d: DiscussionItem }) {
  return (
    <article className="group relative flex gap-4 rounded-2xl border border-border bg-white p-4 shadow-card transition hover:border-navy-200 hover:shadow-lift sm:p-5">
      <div className="hidden size-11 shrink-0 items-center justify-center rounded-xl bg-navy-50 text-navy sm:flex">
        <MessageSquare className="size-5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
          {d.is_pinned && (
            <Badge variant="navy">
              <Pin /> Pinned
            </Badge>
          )}
          <Badge variant="outline">{d.category.name}</Badge>
          {d.area_council && <Badge variant="outline">{d.area_council.short_name}</Badge>}
          {d.is_locked && <Badge variant="outline">Closed</Badge>}
        </div>
        <h3 className="text-base font-bold leading-snug sm:text-lg">
          <Link to={`/community/${d.id}`} className="after:absolute after:inset-0">
            {d.title}
          </Link>
        </h3>
        <p className="mt-1 line-clamp-1 text-sm text-muted-foreground">{d.body}</p>
        <div className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px] text-slate-500">
          <span>
            {d.author.name}
            {d.author.is_team && <span className="ml-1 font-semibold text-green-600">· NIPAM Team</span>}
          </span>
          <span className="flex items-center gap-1">
            <MessageSquare className="size-3.5" /> {d.comment_count}
          </span>
          <span className="flex items-center gap-1">
            <Heart className="size-3.5" /> {d.reaction_count}
          </span>
          <span>{timeAgo(d.last_activity_at)}</span>
        </div>
      </div>
    </article>
  );
}
