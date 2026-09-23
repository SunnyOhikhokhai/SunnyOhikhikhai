import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CalendarPlus, CheckCircle2, Clock, MapPin, Ticket, UserRound, Users, XCircle } from "lucide-react";
import { Link, useLocation, useParams } from "react-router-dom";
import { toast } from "sonner";
import { CoverArt } from "@/components/brand/Artwork";
import { DemoBadge } from "@/components/shared/badges";
import { DateBlock } from "@/components/shared/cards";
import { Markdown } from "@/components/shared/Markdown";
import { Seo } from "@/components/shared/Seo";
import { ShareButton } from "@/components/shared/Share";
import { ErrorState } from "@/components/shared/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useConfirm } from "@/components/ui/confirm";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError, getData } from "@/lib/api";
import type { EventItem } from "@/lib/types";
import { formatDate, formatTime } from "@/lib/utils";
import NotFound from "./NotFound";

function downloadIcs(e: EventItem) {
  const fmt = (iso: string) => new Date(iso).toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
  const end = e.ends_at ?? new Date(new Date(e.starts_at).getTime() + 2 * 3600_000).toISOString();
  const esc = (s: string) => s.replace(/[,;\\]/g, (m) => `\\${m}`).replace(/\n/g, "\\n");
  const ics = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//NIPAM//Events//EN",
    "BEGIN:VEVENT",
    `UID:nipam-event-${e.id}@nipam`,
    `DTSTAMP:${fmt(new Date().toISOString())}`,
    `DTSTART:${fmt(e.starts_at)}`,
    `DTEND:${fmt(end)}`,
    `SUMMARY:${esc(e.title)}`,
    `LOCATION:${esc(e.location)}`,
    `URL:${window.location.href}`,
    `DESCRIPTION:${esc(e.summary)}`,
    "END:VEVENT",
    "END:VCALENDAR",
  ].join("\r\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([ics], { type: "text/calendar" }));
  a.download = `${e.slug}.ics`;
  a.click();
  URL.revokeObjectURL(a.href);
}

export default function EventDetail() {
  const { slug = "" } = useParams();
  const { user } = useAuth();
  const location = useLocation();
  const confirm = useConfirm();
  const qc = useQueryClient();
  const { data: e, isLoading, error, refetch } = useQuery({ queryKey: ["event", slug], queryFn: () => getData<EventItem>(`/api/events/${slug}`) });

  const reg = useMutation({
    mutationFn: (register: boolean) => (register ? api.post(`/api/events/${slug}/register`) : api.del(`/api/events/${slug}/register`)),
    onSuccess: (_, register) => {
      toast.success(register ? "You're registered! We've added this to your notifications." : "Your registration has been cancelled.");
      qc.invalidateQueries({ queryKey: ["event", slug] });
      qc.invalidateQueries({ queryKey: ["events"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  if (error instanceof ApiError && error.status === 404) return <NotFound />;
  if (error) return <div className="container py-16"><ErrorState error={error} onRetry={() => refetch()} /></div>;
  if (isLoading || !e)
    return (
      <div className="container max-w-5xl space-y-5 py-14">
        <Skeleton className="h-12 w-3/4" />
        <Skeleton className="aspect-[16/7]" />
      </div>
    );

  const past = new Date(e.starts_at) < new Date();
  const canRegister = e.status === "published" && e.registration_open && !past;
  const full = e.spots_left === 0;

  let action: React.ReactNode;
  if (e.status === "cancelled") action = <p className="flex items-center gap-2 font-semibold text-red-600"><XCircle className="size-5" /> This event has been cancelled.</p>;
  else if (past) action = <p className="text-sm text-muted-foreground">This event has already taken place.</p>;
  else if (!e.registration_open) action = <p className="text-sm text-muted-foreground">Registration is not required or not yet open for this event.</p>;
  else if (!user)
    action = (
      <Button asChild size="lg" className="w-full">
        <Link to={`/login?next=${encodeURIComponent(location.pathname)}`}><Ticket /> Log in to register</Link>
      </Button>
    );
  else if (!user.email_verified)
    action = (
      <Button asChild size="lg" variant="outline" className="w-full">
        <Link to="/settings?tab=verification">Verify your email to register</Link>
      </Button>
    );
  else if (e.is_registered)
    action = (
      <div className="space-y-3">
        <p className="flex items-center gap-2 font-semibold text-green-700"><CheckCircle2 className="size-5" /> You're registered</p>
        <Button
          variant="outline"
          className="w-full"
          loading={reg.isPending}
          onClick={async () => {
            if (await confirm({ title: "Cancel your registration?", description: "Your place will be released to other members.", confirmLabel: "Cancel registration", destructive: true })) reg.mutate(false);
          }}
        >
          Cancel registration
        </Button>
      </div>
    );
  else
    action = (
      <Button size="lg" className="w-full" disabled={full || !canRegister} loading={reg.isPending} onClick={() => reg.mutate(true)}>
        <Ticket /> {full ? "Fully booked" : "Register"}
      </Button>
    );

  return (
    <article>
      <Seo
        title={e.title}
        description={e.summary}
        image={e.image_url}
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "Event",
          name: e.title,
          startDate: e.starts_at,
          endDate: e.ends_at ?? undefined,
          eventStatus: e.status === "cancelled" ? "https://schema.org/EventCancelled" : "https://schema.org/EventScheduled",
          location: { "@type": "Place", name: e.location, address: `${e.area_council?.name ?? ""}, FCT, Nigeria` },
          organizer: { "@type": "Organization", name: e.organizer },
        }}
      />
      <div className="bg-surface">
        <div className="container max-w-5xl py-10">
          <Link to="/events" className="inline-flex items-center gap-1.5 text-sm font-semibold text-green-600 hover:gap-2.5"><ArrowLeft className="size-4" /> All events</Link>
          <div className="mt-6 flex items-start gap-5">
            <DateBlock iso={e.starts_at} className="hidden sm:flex" />
            <div>
              <div className="mb-3 flex flex-wrap gap-2">
                {e.area_council && <Badge>{e.area_council.name}</Badge>}
                {e.status === "cancelled" && <Badge variant="danger">Cancelled</Badge>}
                {past && <Badge variant="outline">Past event</Badge>}
                {e.is_demo && <DemoBadge />}
              </div>
              <h1 className="text-3xl font-extrabold leading-tight sm:text-4xl">{e.title}</h1>
              <p className="mt-3 text-lg text-muted-foreground">{e.summary}</p>
            </div>
          </div>
        </div>
      </div>
      <div className="container grid max-w-5xl gap-10 py-10 lg:grid-cols-[1fr_320px]">
        <div className="min-w-0 space-y-6">
          <div className="overflow-hidden rounded-2xl border border-border">
            {e.image_url ? <img src={e.image_url} alt="" className="aspect-[16/8] w-full object-cover" /> : <CoverArt seed={e.slug} icon="event" className="aspect-[16/8] w-full" />}
          </div>
          <h2 className="text-2xl font-extrabold">About this event</h2>
          <Markdown>{e.description || e.summary}</Markdown>
        </div>
        <aside className="space-y-5 lg:sticky lg:top-28 lg:self-start">
          <div className="rounded-2xl border border-border bg-white p-6 shadow-card">
            <dl className="space-y-4 text-sm">
              <div className="flex gap-3"><Clock className="size-5 shrink-0 text-green-600" /><div><dt className="font-semibold text-navy">Date & time</dt><dd className="text-slate-600">{formatDate(e.starts_at, { weekday: "long", day: "numeric", month: "long", year: "numeric" })}<br />{formatTime(e.starts_at)}{e.ends_at && ` – ${formatTime(e.ends_at)}`} (WAT)</dd></div></div>
              <div className="flex gap-3"><MapPin className="size-5 shrink-0 text-green-600" /><div><dt className="font-semibold text-navy">Location</dt><dd className="text-slate-600">{e.location}</dd></div></div>
              <div className="flex gap-3"><UserRound className="size-5 shrink-0 text-green-600" /><div><dt className="font-semibold text-navy">Organiser</dt><dd className="text-slate-600">{e.organizer}</dd></div></div>
              {e.registration_open && (
                <div className="flex gap-3"><Users className="size-5 shrink-0 text-green-600" /><div><dt className="font-semibold text-navy">Registration</dt><dd className="text-slate-600">{e.registered_count ?? 0} registered{e.capacity ? ` · ${e.spots_left} of ${e.capacity} places left` : ""}</dd></div></div>
              )}
            </dl>
            <div className="mt-6 border-t border-border pt-5">{action}</div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => downloadIcs(e)} className="flex-1"><CalendarPlus /> Add to calendar</Button>
            <ShareButton title={e.title} text={e.summary} />
          </div>
        </aside>
      </div>
    </article>
  );
}
