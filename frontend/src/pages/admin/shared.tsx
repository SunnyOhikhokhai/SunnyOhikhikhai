import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";
import { Pagination } from "@/components/shared/Pagination";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useDebounce } from "@/hooks/useDebounce";
import { api, type Paged } from "@/lib/api";
import { cn } from "@/lib/utils";

export function AdminTitle({ title, description, actions }: { title: string; description?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-extrabold sm:text-3xl">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

const STATUS_TONE: Record<string, "green" | "default" | "outline" | "danger" | "demo"> = {
  published: "green",
  active: "green",
  visible: "green",
  resolved: "green",
  draft: "outline",
  scheduled: "default",
  open: "demo",
  archived: "outline",
  dismissed: "outline",
  expired: "outline",
  hidden: "demo",
  cancelled: "danger",
  suspended: "danger",
  removed: "danger",
};

export function StatusBadge({ status }: { status: string }) {
  return <Badge variant={STATUS_TONE[status] ?? "default"} className="capitalize">{status.replace("_", " ")}</Badge>;
}

export function useAdminList<T>(key: string, url: string, params: Record<string, string | number | boolean | undefined>) {
  return useQuery({
    queryKey: ["admin", key, params],
    queryFn: () => api.get<Paged<T>>(url, params),
    placeholderData: keepPreviousData,
  });
}

export function SearchBox({ value, onChange, placeholder = "Search" }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <div className="relative w-full sm:w-72">
      <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
      <Input type="search" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="h-10 pl-10" aria-label={placeholder} />
    </div>
  );
}

export function useSearchState() {
  const [q, setQ] = useState("");
  const dq = useDebounce(q, 300);
  return { q, setQ, dq };
}

export interface Column<T> {
  header: string;
  cell: (row: T) => ReactNode;
  className?: string;
}

/** Responsive table: a real table on desktop, stacked cards on mobile. */
export function DataTable<T extends { id?: number | string }>({
  rows,
  columns,
  loading,
  error,
  onRetry,
  empty = "Nothing here yet",
  page,
  totalPages,
  onPage,
  rowKey,
}: {
  rows?: T[];
  columns: Column<T>[];
  loading?: boolean;
  error?: unknown;
  onRetry?: () => void;
  empty?: string;
  page?: number;
  totalPages?: number;
  onPage?: (p: number) => void;
  rowKey?: (r: T) => string | number;
}) {
  if (error) return <ErrorState error={error} onRetry={onRetry} />;
  if (loading && !rows) return <div className="space-y-2">{[0, 1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-14" />)}</div>;
  if (!rows?.length) return <EmptyState title={empty} />;
  const key = (r: T, i: number) => (rowKey ? rowKey(r) : r.id ?? i);
  return (
    <>
      <div className={cn("hidden overflow-x-auto rounded-2xl border border-border bg-white shadow-card md:block", loading && "opacity-60")}>
        <table className="w-full text-sm">
          <thead className="bg-surface text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
            <tr>{columns.map((c) => <th key={c.header} scope="col" className={cn("px-4 py-3", c.className)}>{c.header}</th>)}</tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((r, i) => (
              <tr key={key(r, i)} className="transition hover:bg-surface/60">
                {columns.map((c) => <td key={c.header} className={cn("px-4 py-3 align-middle", c.className)}>{c.cell(r)}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ul className="space-y-3 md:hidden">
        {rows.map((r, i) => (
          <li key={key(r, i)} className="rounded-2xl border border-border bg-white p-4 shadow-card">
            <dl className="space-y-2">
              {columns.map((c) => (
                <div key={c.header} className="flex items-start justify-between gap-3 text-sm">
                  <dt className="shrink-0 text-xs font-semibold uppercase tracking-wider text-slate-500">{c.header}</dt>
                  <dd className="min-w-0 text-right">{c.cell(r)}</dd>
                </div>
              ))}
            </dl>
          </li>
        ))}
      </ul>
      {page && totalPages && onPage ? <Pagination page={page} totalPages={totalPages} onChange={onPage} /> : null}
    </>
  );
}

export function StatCard({ label, value, hint, icon: Icon, tone = "default" }: { label: string; value?: number | string; hint?: string; icon: typeof Search; tone?: "default" | "navy" | "green" }) {
  return (
    <div className={cn("rounded-2xl p-5 shadow-card", tone === "navy" ? "bg-navy text-white" : tone === "green" ? "bg-green-600 text-white" : "border border-border bg-white")}>
      <div className="flex items-center justify-between">
        <p className={cn("text-sm font-medium", tone === "default" ? "text-muted-foreground" : "text-white/80")}>{label}</p>
        <Icon className={cn("size-5", tone === "default" ? "text-green-600" : "text-white/80")} />
      </div>
      <p className={cn("mt-3 font-display text-3xl font-extrabold", tone === "default" ? "text-navy" : "text-white")}>
        {value === undefined ? <Skeleton className="h-8 w-16" /> : typeof value === "number" ? value.toLocaleString("en-NG") : value}
      </p>
      {hint && <p className={cn("mt-1 text-xs", tone === "default" ? "text-slate-500" : "text-white/70")}>{hint}</p>}
    </div>
  );
}

export const CHART = { navy: "#063B66", green: "#079447", deep: "#006B3C", silver: "#9AA0A6", sky: "#4A7FB0", mint: "#5FC98E", grid: "#E3E8EC" };
