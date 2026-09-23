import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { CalendarDays, ChevronLeft, ChevronRight, History, List as ListIcon } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { EventCard } from "@/components/shared/cards";
import { PageHeader } from "@/components/shared/PageHeader";
import { Pagination } from "@/components/shared/Pagination";
import { Seo } from "@/components/shared/Seo";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useMeta } from "@/hooks/useMeta";
import { api, type Paged } from "@/lib/api";
import type { EventItem } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

type Mode = "upcoming" | "past" | "calendar";

function lagosParts(iso: string) {
  const d = new Date(new Date(iso).getTime() + 3600_000);
  return { y: d.getUTCFullYear(), m: d.getUTCMonth(), day: d.getUTCDate() };
}

function Calendar({ month, events, onMonth }: { month: Date; events: EventItem[]; onMonth: (d: Date) => void }) {
  const y = month.getFullYear();
  const m = month.getMonth();
  const first = new Date(y, m, 1);
  const offset = (first.getDay() + 6) % 7; // Monday first
  const days = new Date(y, m + 1, 0).getDate();
  const byDay = useMemo(() => {
    const map = new Map<number, EventItem[]>();
    events.forEach((e) => {
      const p = lagosParts(e.starts_at);
      if (p.y === y && p.m === m) map.set(p.day, [...(map.get(p.day) ?? []), e]);
    });
    return map;
  }, [events, y, m]);
  const today = new Date();
  const [selected, setSelected] = useState<number | null>(null);
  const selectedEvents = selected ? byDay.get(selected) ?? [] : [];

  return (
    <div className="grid gap-8 lg:grid-cols-[1.5fr_1fr]">
      <div className="rounded-2xl border border-border bg-white p-4 shadow-card sm:p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-extrabold">{month.toLocaleDateString("en-NG", { month: "long", year: "numeric" })}</h2>
          <div className="flex gap-2">
            <Button variant="outline" size="icon" aria-label="Previous month" onClick={() => onMonth(new Date(y, m - 1, 1))}><ChevronLeft /></Button>
            <Button variant="outline" size="icon" aria-label="Next month" onClick={() => onMonth(new Date(y, m + 1, 1))}><ChevronRight /></Button>
          </div>
        </div>
        <div className="grid grid-cols-7 gap-1 text-center text-xs font-semibold uppercase text-slate-500" aria-hidden>
          {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => <div key={d} className="py-2">{d}</div>)}
        </div>
        <div className="grid grid-cols-7 gap-1" role="grid">
          {Array.from({ length: offset }).map((_, i) => <div key={`e${i}`} />)}
          {Array.from({ length: days }).map((_, i) => {
            const day = i + 1;
            const evs = byDay.get(day) ?? [];
            const isToday = today.getFullYear() === y && today.getMonth() === m && today.getDate() === day;
            return (
              <button
                key={day}
                role="gridcell"
                onClick={() => setSelected(day)}
                aria-label={`${day} ${month.toLocaleDateString("en-NG", { month: "long" })}${evs.length ? `, ${evs.length} event${evs.length > 1 ? "s" : ""}` : ""}`}
                aria-selected={selected === day}
                className={cn(
                  "relative flex aspect-square flex-col items-center justify-center rounded-xl text-sm font-semibold transition sm:aspect-[1.2]",
                  selected === day ? "bg-navy text-white" : evs.length ? "bg-green-50 text-green-800 hover:bg-green-100" : "text-slate-600 hover:bg-surface",
                  isToday && selected !== day && "ring-2 ring-green-500",
                )}
              >
                {day}
                {evs.length > 0 && <span className={cn("absolute bottom-1.5 size-1.5 rounded-full", selected === day ? "bg-green-300" : "bg-green-600")} />}
              </button>
            );
          })}
        </div>
      </div>
      <div>
        <h3 className="mb-4 text-lg font-bold">
          {selected ? `Events on ${selected} ${month.toLocaleDateString("en-NG", { month: "long" })}` : `${events.length} event${events.length === 1 ? "" : "s"} this month`}
        </h3>
        <div className="space-y-3">
          {(selected ? selectedEvents : events).map((e) => <EventCard key={e.id} event={e} />)}
          {(selected ? selectedEvents : events).length === 0 && <EmptyState title="No events" description="Choose another day or month." icon={CalendarDays} />}
        </div>
      </div>
    </div>
  );
}

export default function Events() {
  const [params, setParams] = useSearchParams();
  const mode = (params.get("view") as Mode) ?? "upcoming";
  const council = params.get("area_council") ?? "";
  const page = Number(params.get("page") ?? 1);
  const [month, setMonth] = useState(() => new Date(new Date().getFullYear(), new Date().getMonth(), 1));
  const meta = useMeta();
  const monthKey = `${month.getFullYear()}-${String(month.getMonth() + 1).padStart(2, "0")}`;

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["events", mode, council, page, mode === "calendar" ? monthKey : null],
    queryFn: () =>
      api.get<Paged<EventItem>>("/api/events", {
        when: mode === "calendar" ? "all" : mode,
        month: mode === "calendar" ? monthKey : undefined,
        area_council: council,
        page,
      }),
    placeholderData: keepPreviousData,
  });
  const set = (k: string, v: string) => {
    const n = new URLSearchParams(params);
    if (v) n.set(k, v);
    else n.delete(k);
    n.delete("page");
    setParams(n);
  };

  return (
    <>
      <Seo title="Events" description="Upcoming and past NIPAM events across the six Area Councils of the FCT." />
      <PageHeader eyebrow="Events" title="Events & gatherings" description="Town halls, forums and community activities across the FCT. Register to secure your place." crumbs={[{ to: "/", label: "Home" }, { label: "Events" }]} />
      <div className="container py-8">
        <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="grid grid-cols-3 rounded-xl bg-surface p-1 ring-1 ring-border sm:inline-grid" role="tablist" aria-label="Event views">
            {([["upcoming", "Upcoming", ListIcon], ["past", "Past", History], ["calendar", "Calendar", CalendarDays]] as const).map(([k, label, Icon]) => (
              <button
                key={k}
                role="tab"
                aria-selected={mode === k}
                onClick={() => set("view", k === "upcoming" ? "" : k)}
                className={cn("flex items-center justify-center gap-1.5 rounded-lg px-2 py-2 text-sm font-semibold transition sm:px-4", mode === k ? "bg-white text-navy shadow-card" : "text-slate-500 hover:text-navy")}
              >
                <Icon className="size-4" /> {label}
              </button>
            ))}
          </div>
          <Select aria-label="Filter by Area Council" value={council} onChange={(e) => set("area_council", e.target.value)} className="sm:w-60">
            <option value="">All Area Councils</option>
            {meta.data?.area_councils.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}
          </Select>
        </div>

        {error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : isLoading || !data ? (
          <div className="grid gap-4 md:grid-cols-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>
        ) : mode === "calendar" ? (
          <Calendar month={month} events={data.data} onMonth={setMonth} />
        ) : data.data.length === 0 ? (
          <EmptyState
            icon={CalendarDays}
            title={mode === "upcoming" ? "No upcoming events" : "No past events"}
            description={mode === "upcoming" ? "New events will be announced soon. Members are notified based on their preferences." : undefined}
            action={<Button asChild variant="outline"><Link to="/events?view=calendar">Open calendar</Link></Button>}
          />
        ) : (
          <>
            {mode === "upcoming" && data.data[0] && (
              <p className="mb-4 text-sm text-muted-foreground">Next event: <strong className="text-navy">{formatDate(data.data[0].starts_at, { weekday: "long", day: "numeric", month: "long" })}</strong></p>
            )}
            <div className="grid gap-4 md:grid-cols-2">{data.data.map((e) => <EventCard key={e.id} event={e} />)}</div>
            <Pagination page={page} totalPages={data.meta.total_pages} onChange={(p) => { const n = new URLSearchParams(params); n.set("page", String(p)); setParams(n); }} />
          </>
        )}
      </div>
    </>
  );
}
