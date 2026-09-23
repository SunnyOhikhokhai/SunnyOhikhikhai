import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CalendarDays, FileText, Loader2, MapPin, MessageSquare, Newspaper, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { useDebounce } from "@/hooks/useDebounce";
import { api } from "@/lib/api";
import type { CouncilRef, DiscussionItem, EventItem, NewsCard, RecordCard } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export interface SearchResults {
  records: RecordCard[];
  news: NewsCard[];
  events: EventItem[];
  councils: CouncilRef[];
  discussions: DiscussionItem[];
}

export function useSearch(q: string, limit = 5, type?: string) {
  const term = useDebounce(q.trim(), 250);
  return useQuery({
    queryKey: ["search", term, limit, type],
    queryFn: () => api.get<{ data: SearchResults; meta: { total: number } }>("/api/search", { q: term, limit, type }),
    enabled: term.length >= 2,
    placeholderData: (prev) => prev,
  });
}

export function GlobalSearch({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const [q, setQ] = useState("");
  const navigate = useNavigate();
  const { data, isFetching } = useSearch(q);
  useEffect(() => {
    if (!open) setQ("");
  }, [open]);

  const groups: { key: keyof SearchResults; label: string; icon: typeof FileText; to: (x: never) => string; title: (x: never) => string; sub: (x: never) => string }[] = [
    { key: "councils", label: "Area Councils", icon: MapPin, to: (c: CouncilRef) => `/area-councils/${c.slug}`, title: (c: CouncilRef) => c.name, sub: () => "Area Council" },
    { key: "records", label: "Our Record", icon: FileText, to: (r: RecordCard) => `/our-record/${r.slug}`, title: (r: RecordCard) => r.title, sub: (r: RecordCard) => `${r.category.name} · ${r.area_council?.short_name ?? "FCT"}` },
    { key: "news", label: "News", icon: Newspaper, to: (n: NewsCard) => `/news/${n.slug}`, title: (n: NewsCard) => n.title, sub: (n: NewsCard) => `${n.category.name} · ${formatDate(n.published_at)}` },
    { key: "events", label: "Events", icon: CalendarDays, to: (e: EventItem) => `/events/${e.slug}`, title: (e: EventItem) => e.title, sub: (e: EventItem) => formatDate(e.starts_at) },
    { key: "discussions", label: "Community", icon: MessageSquare, to: (d: DiscussionItem) => `/community/${d.id}`, title: (d: DiscussionItem) => d.title, sub: (d: DiscussionItem) => d.category.name },
  ];
  const total = data?.meta.total ?? 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="top-[10%] max-w-2xl translate-y-0 p-0 sm:top-[12%]" aria-describedby={undefined}>
        <DialogTitle className="sr-only">Search NIPAM</DialogTitle>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (q.trim().length >= 2) {
              onOpenChange(false);
              navigate(`/search?q=${encodeURIComponent(q.trim())}`);
            }
          }}
          className="flex items-center gap-3 border-b border-border px-5 py-4 pr-14"
        >
          {isFetching ? <Loader2 className="size-5 animate-spin text-green-600" /> : <Search className="size-5 text-slate-400" />}
          <input
            autoFocus
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search records, news, events, councils…"
            className="flex-1 bg-transparent text-base outline-none placeholder:text-slate-400"
            aria-label="Search"
          />
        </form>
        <div className="max-h-[60dvh] overflow-y-auto p-2">
          {q.trim().length < 2 ? (
            <p className="px-4 py-8 text-center text-sm text-muted-foreground">Type at least two characters to search across NIPAM.</p>
          ) : data && total === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-muted-foreground">
              No results for “{q}”. Try a different word, or browse <Link to="/our-record" onClick={() => onOpenChange(false)} className="font-semibold text-green-600">Our Record</Link>.
            </p>
          ) : (
            data &&
            groups.map((g) => {
              const items = data.data[g.key] as never[];
              if (!items?.length) return null;
              const Icon = g.icon;
              return (
                <div key={g.key} className="mb-2">
                  <p className="px-3 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">{g.label}</p>
                  {items.map((item, i) => (
                    <Link key={i} to={g.to(item)} onClick={() => onOpenChange(false)} className="flex items-center gap-3 rounded-xl px-3 py-2.5 transition hover:bg-navy-50 focus:bg-navy-50">
                      <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-surface text-navy">
                        <Icon className="size-4" />
                      </span>
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-semibold text-navy">{g.title(item)}</span>
                        <span className="block truncate text-xs text-muted-foreground">{g.sub(item)}</span>
                      </span>
                    </Link>
                  ))}
                </div>
              );
            })
          )}
          {total > 0 && (
            <Link
              to={`/search?q=${encodeURIComponent(q.trim())}`}
              onClick={() => onOpenChange(false)}
              className="mt-1 flex items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold text-green-600 hover:bg-green-50"
            >
              See all results <ArrowRight className="size-4" />
            </Link>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
