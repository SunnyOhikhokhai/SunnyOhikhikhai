import { useQuery } from "@tanstack/react-query";
import { AlertCircle, ArrowRight, Bell, CalendarDays, FileText, MapPin, Megaphone, MessageSquare, Newspaper, Settings, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { DiscussionRow, EventCard, NewsCard, RecordCard } from "@/components/shared/cards";
import { Seo } from "@/components/shared/Seo";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getData } from "@/lib/api";
import type { Announcement, Council, DiscussionItem, EventItem, Me, NewsCard as NewsCardT, NotificationItem, RecordCard as RecordCardT } from "@/lib/types";
import { cn, timeAgo } from "@/lib/utils";

interface DashboardData {
  user: Me;
  area_council: Council | null;
  announcements: Announcement[];
  latest_updates: NewsCardT[];
  upcoming_events: EventItem[];
  my_event_count: number;
  featured_records: RecordCardT[];
  notifications: NotificationItem[];
  unread_notifications: number;
  discussions: DiscussionItem[];
}

function Panel({ title, icon: Icon, action, children, className }: { title: string; icon: typeof Bell; action?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <section className={cn("rounded-2xl border border-border bg-white p-5 shadow-card sm:p-6", className)} aria-label={title}>
      <div className="mb-5 flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2.5 text-lg font-extrabold">
          <span className="flex size-8 items-center justify-center rounded-lg bg-navy-50 text-navy"><Icon className="size-4" /></span>
          {title}
        </h2>
        {action}
      </div>
      {children}
    </section>
  );
}

const more = (to: string, label = "View all") => (
  <Link to={to} className="inline-flex items-center gap-1 text-sm font-semibold text-green-600 hover:gap-2">
    {label} <ArrowRight className="size-3.5" />
  </Link>
);

export default function Dashboard() {
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["dashboard"], queryFn: () => getData<DashboardData>("/api/members/dashboard") });
  if (error) return <div className="container py-16"><ErrorState error={error} onRetry={() => refetch()} /></div>;

  const hour = Number(new Intl.DateTimeFormat("en-NG", { hour: "numeric", hour12: false, timeZone: "Africa/Lagos" }).format(new Date()));
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <div className="bg-surface pb-16">
      <Seo title="My dashboard" noindex />
      <div className="bg-navy pb-24 pt-10 text-white">
        <div className="container">
          <p className="text-sm font-medium text-green-300">{greeting}</p>
          <h1 className="mt-1 text-3xl font-extrabold text-white sm:text-4xl">
            Welcome, {data ? data.user.first_name : <Skeleton className="inline-block h-8 w-32 bg-white/10 align-middle" />}
          </h1>
          <p className="mt-2 text-navy-100">Here's what's happening across NIPAM and your Area Council.</p>
        </div>
      </div>
      <div className="container -mt-16 space-y-6">
        {data && !data.user.email_verified && (
          <div className="flex flex-col gap-3 rounded-2xl bg-amber-50 p-5 ring-1 ring-amber-200 sm:flex-row sm:items-center">
            <AlertCircle className="size-6 shrink-0 text-amber-600" />
            <p className="flex-1 text-sm text-amber-900"><strong>Verify your email</strong> to register for events and take part in community discussions.</p>
            <Button asChild size="sm" variant="navy"><Link to="/settings?tab=verification">Verify now</Link></Button>
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-green-600 to-green-800 p-6 text-white shadow-lift lg:col-span-1" aria-label="My Area Council">
            <div className="pointer-events-none absolute -right-10 -top-10 size-40 rounded-full border-[18px] border-white/10" />
            <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-green-100"><MapPin className="size-3.5" /> My Area Council</p>
            {isLoading ? (
              <Skeleton className="mt-3 h-8 w-40 bg-white/20" />
            ) : data?.area_council ? (
              <>
                <h2 className="mt-2 text-2xl font-extrabold text-white">{data.area_council.name}</h2>
                <p className="mt-2 line-clamp-2 text-sm text-green-50">{data.area_council.summary}</p>
                <p className="mt-4 flex items-center gap-2 text-sm text-green-50"><Users className="size-4" /> {data.area_council.member_count} member{data.area_council.member_count === 1 ? "" : "s"}</p>
                <div className="mt-5 flex flex-wrap gap-2">
                  <Button asChild size="sm" variant="white"><Link to={`/area-councils/${data.area_council.slug}`}>Open council page</Link></Button>
                  <Button asChild size="sm" variant="outline-light"><Link to="/settings">Change</Link></Button>
                </div>
              </>
            ) : (
              <>
                <h2 className="mt-2 text-xl font-bold text-white">No Area Council selected</h2>
                <Button asChild size="sm" variant="white" className="mt-4"><Link to="/settings">Choose your council</Link></Button>
              </>
            )}
          </section>

          <div className="grid gap-4 sm:grid-cols-3 lg:col-span-2">
            {[
              { icon: Bell, label: "Unread notifications", value: data?.unread_notifications, to: "/notifications" },
              { icon: CalendarDays, label: "Events you're attending", value: data?.my_event_count, to: "/events" },
              { icon: Settings, label: "Communication settings", value: "Manage", to: "/settings?tab=notifications" },
            ].map(({ icon: Icon, label, value, to }) => (
              <Link key={label} to={to} className="group flex flex-col justify-between rounded-2xl border border-border bg-white p-5 shadow-card transition hover:-translate-y-0.5 hover:shadow-lift">
                <Icon className="size-6 text-green-600" />
                <div className="mt-6">
                  <p className="font-display text-3xl font-extrabold text-navy">{value ?? <Skeleton className="h-8 w-10" />}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{label}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {data?.announcements && data.announcements.length > 0 && (
          <div className="space-y-2">
            {data.announcements.map((a) => (
              <div key={a.id} className={cn("flex items-start gap-3 rounded-2xl p-4 ring-1", a.priority === "important" ? "bg-navy text-white ring-navy" : "bg-white ring-border")}>
                <Megaphone className={cn("mt-0.5 size-5 shrink-0", a.priority === "important" ? "text-green-300" : "text-green-600")} />
                <div className="flex-1 text-sm">
                  <p className="font-bold">{a.title}</p>
                  <p className={a.priority === "important" ? "text-navy-100" : "text-muted-foreground"}>{a.body}</p>
                </div>
                {a.link_url && <Link to={a.link_url} className="text-sm font-semibold text-green-500 hover:underline">Open</Link>}
              </div>
            ))}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
          <Panel title="Latest updates" icon={Newspaper} action={more("/news")}>
            {isLoading ? <Skeleton className="h-60" /> : data?.latest_updates.length ? (
              <div className="grid gap-5 sm:grid-cols-2">{data.latest_updates.slice(0, 4).map((n) => <NewsCard key={n.id} item={n} compact />)}</div>
            ) : <EmptyState title="No updates yet" />}
          </Panel>
          <div className="space-y-6">
            <Panel title="Notifications" icon={Bell} action={more("/notifications")}>
              {isLoading ? <Skeleton className="h-40" /> : data?.notifications.length ? (
                <ul className="divide-y divide-border">
                  {data.notifications.map((n) => (
                    <li key={n.id} className="py-3 first:pt-0 last:pb-0">
                      <Link to={n.link ?? "/notifications"} className="group flex gap-3">
                        <span className={cn("mt-1.5 size-2 shrink-0 rounded-full", n.read ? "bg-transparent" : "bg-green-500")} aria-label={n.read ? undefined : "Unread"} />
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-semibold text-navy group-hover:text-green-600">{n.title}</span>
                          <span className="block text-xs text-slate-500">{timeAgo(n.created_at)}</span>
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : <p className="text-sm text-muted-foreground">You're all caught up.</p>}
            </Panel>
            <Panel title="Upcoming events" icon={CalendarDays} action={more("/events")}>
              {isLoading ? <Skeleton className="h-40" /> : data?.upcoming_events.length ? (
                <div className="space-y-3">{data.upcoming_events.slice(0, 3).map((e) => <EventCard key={e.id} event={e} className="shadow-none" />)}</div>
              ) : <p className="text-sm text-muted-foreground">No upcoming events.</p>}
            </Panel>
          </div>
        </div>

        <Panel title="Featured records" icon={FileText} action={more("/our-record", "Explore Our Record")}>
          {isLoading ? <Skeleton className="h-60" /> : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">{data?.featured_records.map((r) => <RecordCard key={r.id} record={r} />)}</div>
          )}
        </Panel>

        <Panel title="Community" icon={MessageSquare} action={more("/community", "Join the conversation")}>
          {isLoading ? <Skeleton className="h-40" /> : data?.discussions.length ? (
            <div className="grid gap-4 lg:grid-cols-2">{data.discussions.map((d) => <DiscussionRow key={d.id} d={d} />)}</div>
          ) : <EmptyState title="No discussions yet" action={<Button asChild><Link to="/community?new=1">Start one</Link></Button>} />}
        </Panel>
      </div>
    </div>
  );
}
