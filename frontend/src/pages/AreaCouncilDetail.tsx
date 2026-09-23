import { useQuery } from "@tanstack/react-query";
import { Building2, CalendarDays, FileText, Info, Landmark, Megaphone, MessageSquare, Newspaper, Plus, Users } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { DiscussionRow, EventCard, NewsCard, RecordCard } from "@/components/shared/cards";
import { Markdown } from "@/components/shared/Markdown";
import { PageHeader } from "@/components/shared/PageHeader";
import { Seo } from "@/components/shared/Seo";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/hooks/useAuth";
import { ApiError, getData } from "@/lib/api";
import type { Announcement, Council, DiscussionItem, EventItem, NewsCard as NewsCardT, RecordCard as RecordCardT } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import NotFound from "./NotFound";

interface CouncilPage {
  council: Council;
  updates: NewsCardT[];
  public_information: NewsCardT[];
  events: EventItem[];
  records: RecordCardT[];
  discussions: DiscussionItem[];
  announcements: Announcement[];
}

function Grid({ children }: { children: React.ReactNode }) {
  return <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">{children}</div>;
}

export default function AreaCouncilDetail() {
  const { slug = "" } = useParams();
  const { user } = useAuth();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["council", slug],
    queryFn: () => getData<CouncilPage>(`/api/area-councils/${slug}`),
  });
  if (error instanceof ApiError && error.status === 404) return <NotFound />;
  const c = data?.council;
  const isMine = user?.area_council?.slug === slug;

  return (
    <>
      <Seo title={c ? c.name : "Area Council"} description={c?.summary} />
      <PageHeader
        eyebrow="Area Council"
        title={c ? c.name : <Skeleton className="h-10 w-72 bg-white/10" />}
        description={c?.summary}
        crumbs={[{ to: "/", label: "Home" }, { to: "/area-councils", label: "Area Councils" }, { label: c?.short_name ?? "…" }]}
        actions={
          isMine ? (
            <span className="rounded-full bg-green-600 px-4 py-2 text-sm font-semibold text-white">Your Area Council</span>
          ) : !user ? (
            <Button asChild>
              <Link to="/join">Join NIPAM</Link>
            </Button>
          ) : null
        }
      >
        {c && (
          <dl className="mt-8 flex flex-wrap gap-3">
            <div className="flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2.5 text-sm ring-1 ring-white/15">
              <Users className="size-4 text-green-300" />
              <dt className="sr-only">Members</dt>
              <dd>{c.member_count ?? 0} member{c.member_count === 1 ? "" : "s"}</dd>
            </div>
            {c.headquarters && (
              <div className="flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2.5 text-sm ring-1 ring-white/15">
                <Landmark className="size-4 text-green-300" />
                <dt className="sr-only">Headquarters</dt>
                <dd>Headquarters: {c.headquarters}</dd>
              </div>
            )}
          </dl>
        )}
      </PageHeader>

      <div className="container py-10">
        {error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : isLoading || !data ? (
          <div className="space-y-4">
            <Skeleton className="h-12" />
            <Skeleton className="h-64" />
          </div>
        ) : (
          <Tabs defaultValue="overview">
            <TabsList aria-label="Council sections">
              <TabsTrigger value="overview"><Info /> Overview</TabsTrigger>
              <TabsTrigger value="updates"><Newspaper /> Community Updates</TabsTrigger>
              <TabsTrigger value="events"><CalendarDays /> Events</TabsTrigger>
              <TabsTrigger value="info"><Building2 /> Public Information</TabsTrigger>
              <TabsTrigger value="records"><FileText /> Projects/Records</TabsTrigger>
              <TabsTrigger value="discussions"><MessageSquare /> Discussions</TabsTrigger>
              <TabsTrigger value="announcements"><Megaphone /> Announcements</TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <div className="grid gap-8 lg:grid-cols-[1.6fr_1fr]">
                <div className="rounded-2xl border border-border bg-white p-6 shadow-card sm:p-8">
                  <h2 className="text-2xl font-extrabold">About {data.council.short_name}</h2>
                  <Markdown className="mt-2">{data.council.description}</Markdown>
                  {data.council.wards.length > 0 && (
                    <>
                      <h3 className="mt-6 text-lg font-bold">Wards</h3>
                      <ul className="mt-3 flex flex-wrap gap-2">
                        {data.council.wards.map((w) => (
                          <li key={w} className="rounded-full bg-surface px-3 py-1 text-sm text-slate-700 ring-1 ring-border">{w}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
                <aside className="space-y-4">
                  <div className="rounded-2xl bg-navy p-6 text-white">
                    <h3 className="text-lg font-bold text-white">At a glance</h3>
                    <ul className="mt-4 space-y-2.5 text-sm text-navy-100">
                      <li className="flex justify-between"><span>Upcoming events</span><strong className="text-white">{data.events.length}</strong></li>
                      <li className="flex justify-between"><span>Documented records</span><strong className="text-white">{data.records.length}</strong></li>
                      <li className="flex justify-between"><span>Community discussions</span><strong className="text-white">{data.discussions.length}</strong></li>
                      <li className="flex justify-between"><span>Active announcements</span><strong className="text-white">{data.announcements.length}</strong></li>
                    </ul>
                  </div>
                  {data.updates[0] && <NewsCard item={data.updates[0]} compact />}
                </aside>
              </div>
            </TabsContent>

            <TabsContent value="updates">
              {data.updates.length ? <Grid>{data.updates.map((n) => <NewsCard key={n.id} item={n} />)}</Grid> : <EmptyState title="No community updates yet" icon={Newspaper} />}
            </TabsContent>
            <TabsContent value="events">
              {data.events.length ? (
                <div className="grid gap-4 md:grid-cols-2">{data.events.map((e) => <EventCard key={e.id} event={e} />)}</div>
              ) : (
                <EmptyState title="No upcoming events" icon={CalendarDays} action={<Button asChild variant="outline"><Link to="/events">See all events</Link></Button>} />
              )}
            </TabsContent>
            <TabsContent value="info">
              {data.public_information.length ? (
                <Grid>{data.public_information.map((n) => <NewsCard key={n.id} item={n} />)}</Grid>
              ) : (
                <EmptyState title="No public information notices yet" icon={Building2} />
              )}
            </TabsContent>
            <TabsContent value="records">
              {data.records.length ? (
                <>
                  <Grid>{data.records.map((r) => <RecordCard key={r.id} record={r} />)}</Grid>
                  <div className="mt-8 text-center">
                    <Button asChild variant="outline"><Link to={`/our-record?area_council=${slug}`}>All {data.council.short_name} records</Link></Button>
                  </div>
                </>
              ) : (
                <EmptyState title="No records documented yet" icon={FileText} />
              )}
            </TabsContent>
            <TabsContent value="discussions">
              <div className="mb-5 flex justify-end">
                <Button asChild size="sm"><Link to={`/community?new=1&area_council=${slug}`}><Plus /> Start a discussion</Link></Button>
              </div>
              {data.discussions.length ? (
                <div className="space-y-4">{data.discussions.map((d) => <DiscussionRow key={d.id} d={d} />)}</div>
              ) : (
                <EmptyState title="No discussions yet" description={`Start the first conversation for ${data.council.short_name}.`} icon={MessageSquare} />
              )}
            </TabsContent>
            <TabsContent value="announcements">
              {data.announcements.length ? (
                <ul className="space-y-3">
                  {data.announcements.map((a) => (
                    <li key={a.id} className="rounded-2xl border border-border bg-white p-5 shadow-card">
                      <div className="flex items-start gap-3">
                        <Megaphone className="mt-0.5 size-5 text-green-600" />
                        <div>
                          <p className="font-bold text-navy">{a.title}</p>
                          <p className="mt-1 text-sm text-muted-foreground">{a.body}</p>
                          <p className="mt-2 text-xs text-slate-500">Published {formatDate(a.publish_at ?? a.created_at)}</p>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState title="No active announcements" icon={Megaphone} />
              )}
            </TabsContent>
          </Tabs>
        )}
      </div>
    </>
  );
}
