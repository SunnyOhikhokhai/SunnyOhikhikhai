import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CalendarDays, CheckCheck, Megaphone, MessageSquare, Settings, ShieldCheck, MapPin } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { PageHeader } from "@/components/shared/PageHeader";
import { Pagination } from "@/components/shared/Pagination";
import { Seo } from "@/components/shared/Seo";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { api, type Paged } from "@/lib/api";
import type { NotificationItem } from "@/lib/types";
import { cn, timeAgo } from "@/lib/utils";

const TYPES: Record<NotificationItem["type"], { label: string; icon: typeof Bell }> = {
  announcement: { label: "Announcements", icon: Megaphone },
  event: { label: "Events", icon: CalendarDays },
  community: { label: "Community", icon: MessageSquare },
  account: { label: "Account", icon: ShieldCheck },
  council_update: { label: "Area Council", icon: MapPin },
};

export default function Notifications() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [type, setType] = useState<string>("");
  const [unread, setUnread] = useState(false);
  const [page, setPage] = useState(1);
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["notifications", "list", type, unread, page],
    queryFn: () => api.get<Paged<NotificationItem>>("/api/notifications", { type, unread: unread || undefined, page }),
    placeholderData: keepPreviousData,
  });
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["notifications"] });
    qc.invalidateQueries({ queryKey: ["dashboard"] });
  };
  const readAll = useMutation({ mutationFn: () => api.post("/api/notifications/read-all"), onSuccess: invalidate });
  const open = async (n: NotificationItem) => {
    if (!n.read) {
      await api.post(`/api/notifications/${n.id}/read`);
      invalidate();
    }
    if (n.link) navigate(n.link);
  };

  return (
    <>
      <Seo title="Notifications" noindex />
      <PageHeader
        eyebrow="Notification centre"
        title="Notifications"
        description={data ? `${data.meta.unread ?? 0} unread` : undefined}
        actions={
          <>
            <Button variant="outline-light" onClick={() => readAll.mutate()} loading={readAll.isPending} disabled={!data?.meta.unread}><CheckCheck /> Mark all as read</Button>
            <Button asChild variant="white"><Link to="/settings?tab=notifications"><Settings /> Preferences</Link></Button>
          </>
        }
      />
      <div className="container max-w-4xl py-8">
        <div className="mb-6 flex flex-wrap items-center gap-2">
          {[["", "All"], ...Object.entries(TYPES).map(([k, v]) => [k, v.label])].map(([k, label]) => (
            <button key={k} onClick={() => { setType(k); setPage(1); }} aria-pressed={type === k} className={cn("rounded-full px-4 py-2 text-sm font-semibold", type === k ? "bg-navy text-white" : "bg-surface text-slate-600 ring-1 ring-border")}>
              {label}
            </button>
          ))}
          <label className="ml-auto flex items-center gap-2 text-sm font-medium text-slate-600">
            <input type="checkbox" checked={unread} onChange={(e) => { setUnread(e.target.checked); setPage(1); }} className="size-4 accent-green-600" /> Unread only
          </label>
        </div>
        {error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : isLoading ? (
          <div className="space-y-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-20" />)}</div>
        ) : !data?.data.length ? (
          <EmptyState icon={Bell} title="No notifications" description="Announcements, event updates and replies to your posts will appear here." />
        ) : (
          <ul className="overflow-hidden rounded-2xl border border-border bg-white shadow-card">
            {data.data.map((n) => {
              const T = TYPES[n.type] ?? TYPES.account;
              return (
                <li key={n.id} className="border-b border-border last:border-0">
                  <button onClick={() => open(n)} className={cn("flex w-full gap-4 p-4 text-left transition hover:bg-surface sm:p-5", !n.read && "bg-green-50/40")}>
                    <span className={cn("flex size-10 shrink-0 items-center justify-center rounded-xl", n.read ? "bg-surface text-slate-500" : "bg-navy text-white")}>
                      <T.icon className="size-5" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-start justify-between gap-3">
                        <span className={cn("text-sm", n.read ? "font-medium text-slate-700" : "font-bold text-navy")}>{n.title}</span>
                        <span className="shrink-0 text-xs text-slate-500">{timeAgo(n.created_at)}</span>
                      </span>
                      {n.body && <span className="mt-0.5 block text-sm text-muted-foreground">{n.body}</span>}
                      <span className="mt-1 block text-xs font-medium text-slate-400">{T.label}{!n.read && <span className="ml-2 text-green-600">● Unread</span>}</span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
        {data && <Pagination page={page} totalPages={data.meta.total_pages} onChange={setPage} />}
      </div>
    </>
  );
}
