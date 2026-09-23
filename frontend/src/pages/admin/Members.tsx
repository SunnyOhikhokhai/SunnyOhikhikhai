import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BadgeCheck, CircleDashed, Download, Eye } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, Textarea } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { useMeta } from "@/hooks/useMeta";
import { api, getData } from "@/lib/api";
import type { CouncilRef } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { AdminTitle, DataTable, SearchBox, StatusBadge, useAdminList, useSearchState } from "./shared";

interface Member {
  id: number;
  full_name: string;
  email?: string;
  phone?: string | null;
  status: string;
  suspended_reason: string | null;
  email_verified: boolean;
  phone_verified: boolean;
  area_council: CouncilRef | null;
  ward: string | null;
  created_at: string;
  last_login_at: string | null;
  role: string | null;
  preferences: Record<string, boolean> | null;
  activity?: { discussions: number; comments: number; reports_against: number };
}

function MemberDrawer({ id, onClose }: { id: number | null; onClose: () => void }) {
  const { can } = useAuth();
  const qc = useQueryClient();
  const [reason, setReason] = useState("");
  const { data: m } = useQuery({ queryKey: ["admin", "member", id], queryFn: () => getData<Member>(`/api/admin/members/${id}`), enabled: !!id });
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["admin", "member", id] });
    qc.invalidateQueries({ queryKey: ["admin", "members"] });
  };
  const suspend = useMutation({
    mutationFn: () => api.post(`/api/admin/members/${id}/suspend`, { reason }),
    onSuccess: () => { toast.success("Member suspended and signed out"); setReason(""); refresh(); },
    onError: (e: Error) => toast.error(e.message),
  });
  const reactivate = useMutation({
    mutationFn: () => api.post(`/api/admin/members/${id}/reactivate`),
    onSuccess: () => { toast.success("Member reactivated"); refresh(); },
    onError: (e: Error) => toast.error(e.message),
  });
  const optOut = useMutation({
    mutationFn: (key: string) => api.put(`/api/admin/members/${id}/preferences`, { [key]: false }),
    onSuccess: () => { toast.success("Opt-out recorded"); refresh(); },
  });
  return (
    <Dialog open={!!id} onOpenChange={(o) => !o && onClose()}>
      <DialogContent side="right" className="p-6">
        {!m ? <Skeleton className="h-96" /> : (
          <div className="space-y-6">
            <DialogHeader>
              <DialogTitle>{m.full_name}</DialogTitle>
              <DialogDescription>Member since {formatDate(m.created_at)}</DialogDescription>
            </DialogHeader>
            <dl className="space-y-3 text-sm">
              {[
                ["Status", <StatusBadge key="s" status={m.status} />],
                ["Area Council", m.area_council?.name ?? "—"],
                ["Ward", m.ward ?? "—"],
                ...(m.email !== undefined ? [["Email", `${m.email} ${m.email_verified ? "✓" : "(unverified)"}`], ["Phone", m.phone ? `${m.phone} ${m.phone_verified ? "✓" : "(unverified)"}` : "—"]] : []),
                ["Last login", m.last_login_at ? formatDate(m.last_login_at) : "—"],
                ["Admin role", m.role ?? "—"],
              ].map(([k, v]) => (
                <div key={String(k)} className="flex justify-between gap-4 border-b border-border pb-2"><dt className="text-slate-500">{k}</dt><dd className="text-right font-medium text-navy">{v}</dd></div>
              ))}
            </dl>
            {m.activity && (
              <div className="grid grid-cols-3 gap-2 text-center">
                {[["Discussions", m.activity.discussions], ["Comments", m.activity.comments], ["Reports", m.activity.reports_against]].map(([k, v]) => (
                  <div key={k} className="rounded-xl bg-surface p-3"><p className="font-display text-xl font-extrabold text-navy">{v}</p><p className="text-xs text-slate-500">{k}</p></div>
                ))}
              </div>
            )}
            {m.suspended_reason && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">Suspended: {m.suspended_reason}</p>}
            {can("members.view") && m.preferences && (
              <div>
                <p className="mb-2 text-sm font-semibold text-navy">Communication preferences</p>
                <ul className="space-y-1.5 text-sm">
                  {Object.entries(m.preferences).filter(([k]) => !k.startsWith("in_app")).map(([k, v]) => (
                    <li key={k} className="flex items-center justify-between">
                      <span className="text-slate-600">{k.replace("_", " · ").replace("_", " ")}</span>
                      {v ? <button className="text-xs font-semibold text-red-600 hover:underline" onClick={() => optOut.mutate(k)}>Record opt-out</button> : <span className="text-xs text-slate-400">Off</span>}
                    </li>
                  ))}
                </ul>
                <p className="mt-2 text-xs text-muted-foreground">Admins can record opt-outs on a member's request but can never opt members in.</p>
              </div>
            )}
            {can("members.suspend") && (
              m.status === "active" ? (
                <div className="space-y-2 rounded-xl border border-red-200 p-4">
                  <Label htmlFor="reason">Suspend account</Label>
                  <Textarea id="reason" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Reason (recorded in the audit log)" className="min-h-[70px]" />
                  <Button variant="destructive" size="sm" disabled={reason.length < 3} loading={suspend.isPending} onClick={() => suspend.mutate()}>Suspend and sign out</Button>
                </div>
              ) : (
                <Button onClick={() => reactivate.mutate()} loading={reactivate.isPending}>Reactivate account</Button>
              )
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function Members() {
  const { can } = useAuth();
  const meta = useMeta();
  const { q, setQ, dq } = useSearchState();
  const [council, setCouncil] = useState("");
  const [status, setStatus] = useState("");
  const [verified, setVerified] = useState("");
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState<number | null>(null);
  const { data, isLoading, error, refetch } = useAdminList<Member>("members", "/api/admin/members", { q: dq, area_council: council, status, verified, page });
  const showContact = can("members.view");

  const exportCsv = async () => {
    const res = await api.download(`/api/admin/members/export${council ? `?area_council=${council}` : ""}`);
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "nipam-members.csv";
    a.click();
    toast.success("Export downloaded. This action has been logged.");
  };

  return (
    <>
      <AdminTitle
        title="Members"
        description={data ? `${data.meta.total.toLocaleString()} members` : undefined}
        actions={can("members.export") && <Button variant="outline" onClick={exportCsv}><Download /> Export permitted data</Button>}
      />
      <div className="mb-5 grid gap-2 sm:flex sm:flex-wrap">
        <SearchBox value={q} onChange={(v) => { setQ(v); setPage(1); }} placeholder={showContact ? "Name, email or phone" : "Search by name"} />
        <Select value={council} onChange={(e) => { setCouncil(e.target.value); setPage(1); }} className="h-10 sm:w-48" aria-label="Area Council">
          <option value="">All councils</option>
          {meta.data?.area_councils.map((c) => <option key={c.slug} value={c.slug}>{c.short_name}</option>)}
        </Select>
        <Select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="h-10 sm:w-40" aria-label="Status">
          <option value="">Any status</option><option value="active">Active</option><option value="suspended">Suspended</option>
        </Select>
        <Select value={verified} onChange={(e) => { setVerified(e.target.value); setPage(1); }} className="h-10 sm:w-44" aria-label="Verification">
          <option value="">Any verification</option><option value="true">Verified</option><option value="false">Unverified</option>
        </Select>
      </div>
      <DataTable
        rows={data?.data}
        loading={isLoading}
        error={error}
        onRetry={() => refetch()}
        empty="No members match these filters"
        page={page}
        totalPages={data?.meta.total_pages}
        onPage={setPage}
        columns={[
          { header: "Name", cell: (m) => <span className="font-semibold text-navy">{m.full_name}</span> },
          ...(showContact ? [{ header: "Email", cell: (m: Member) => <span className="text-slate-600">{m.email}</span> }] : []),
          { header: "Area Council", cell: (m) => m.area_council?.short_name ?? "—" },
          { header: "Verified", cell: (m) => (m.email_verified ? <BadgeCheck className="inline size-5 text-green-600" aria-label="Verified" /> : <CircleDashed className="inline size-5 text-slate-400" aria-label="Unverified" />) },
          { header: "Status", cell: (m) => <StatusBadge status={m.status} /> },
          { header: "Joined", cell: (m) => formatDate(m.created_at) },
          { header: "", className: "text-right", cell: (m) => <Button size="sm" variant="ghost" onClick={() => setOpen(m.id)}><Eye /> View</Button> },
        ]}
      />
      <MemberDrawer id={open} onClose={() => setOpen(null)} />
    </>
  );
}
