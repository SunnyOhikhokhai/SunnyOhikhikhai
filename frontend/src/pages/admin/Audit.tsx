import { useState } from "react";
import { formatDateTime } from "@/lib/utils";
import { AdminTitle, DataTable, SearchBox, useAdminList, useSearchState } from "./shared";

interface Log { id: number; actor: string; action: string; target_type: string | null; target_id: number | null; ip_address: string | null; meta: Record<string, unknown>; created_at: string }

export default function Audit() {
  const { q, setQ, dq } = useSearchState();
  const [page, setPage] = useState(1);
  const { data, isLoading, error, refetch } = useAdminList<Log>("audit", "/api/admin/audit-logs", { action: dq, page });
  return (
    <>
      <AdminTitle title="Audit log" description="A permanent record of administrative and security-relevant actions." />
      <div className="mb-5"><SearchBox value={q} onChange={setQ} placeholder="Filter by action, e.g. member." /></div>
      <DataTable
        rows={data?.data}
        loading={isLoading}
        error={error}
        onRetry={() => refetch()}
        page={page}
        totalPages={data?.meta.total_pages}
        onPage={setPage}
        columns={[
          { header: "When", cell: (l) => <span className="whitespace-nowrap">{formatDateTime(l.created_at)}</span> },
          { header: "Actor", cell: (l) => l.actor },
          { header: "Action", cell: (l) => <code className="rounded bg-surface px-1.5 py-0.5 text-xs text-navy">{l.action}</code> },
          { header: "Target", cell: (l) => (l.target_type ? `${l.target_type} #${l.target_id ?? ""}` : "—") },
          { header: "Details", cell: (l) => <span className="line-clamp-2 max-w-xs break-all text-xs text-slate-500">{Object.keys(l.meta ?? {}).length ? JSON.stringify(l.meta) : "—"}</span> },
          { header: "IP", cell: (l) => <span className="text-xs text-slate-500">{l.ip_address ?? "—"}</span> },
        ]}
      />
    </>
  );
}
