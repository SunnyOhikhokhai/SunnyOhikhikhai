import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Megaphone, Pencil, Send, TimerOff, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useConfirm } from "@/components/ui/confirm";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input, Select, Textarea } from "@/components/ui/input";
import { Field } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { useMeta } from "@/hooks/useMeta";
import { api } from "@/lib/api";
import type { Announcement } from "@/lib/types";
import { formatDateTime, fromLocalInput, toLocalInput } from "@/lib/utils";
import { AdminTitle, DataTable, StatusBadge, useAdminList } from "./shared";

function effectiveStatus(a: Announcement) {
  const now = Date.now();
  if (a.expires_at && new Date(a.expires_at).getTime() <= now) return "expired";
  if (a.status === "published" && a.publish_at && new Date(a.publish_at).getTime() > now) return "scheduled";
  return a.status;
}

export default function Announcements() {
  const { user } = useAuth();
  const scoped = user?.admin?.role === "area_council_admin" ? user.admin.area_council?.slug ?? "" : "";
  const meta = useMeta();
  const qc = useQueryClient();
  const confirm = useConfirm();
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<Announcement | "new" | null>(null);
  const blank = { title: "", body: "", link_url: "", area_council: scoped, priority: "normal", publish_at: "", expires_at: "" };
  const [f, setF] = useState(blank);
  const { data, isLoading, error, refetch } = useAdminList<Announcement>("announcements", "/api/admin/announcements", { page });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["admin", "announcements"] });

  const open = (a: Announcement | "new") => {
    setEditing(a);
    setF(a === "new" ? blank : { title: a.title, body: a.body, link_url: a.link_url ?? "", area_council: a.area_council?.slug ?? "", priority: a.priority, publish_at: toLocalInput(a.publish_at), expires_at: toLocalInput(a.expires_at) });
  };
  const save = useMutation({
    mutationFn: () => {
      const body = { ...f, link_url: f.link_url || null, area_council: f.area_council || null, publish_at: fromLocalInput(f.publish_at), expires_at: fromLocalInput(f.expires_at) };
      return editing === "new" ? api.post("/api/admin/announcements", body) : api.put(`/api/admin/announcements/${(editing as Announcement).id}`, body);
    },
    onSuccess: () => { toast.success("Announcement saved as draft"); setEditing(null); invalidate(); },
    onError: (e: Error) => toast.error(e.message),
  });
  const act = useMutation({
    mutationFn: ({ id, a }: { id: number; a: "publish" | "expire" }) => api.post(`/api/admin/announcements/${id}/${a}`),
    onSuccess: (_, v) => { toast.success(v.a === "publish" ? "Published — members will be notified at the publish time" : "Announcement expired"); invalidate(); },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <>
      <AdminTitle title="Announcements" description="Create, schedule, publish and expire announcements. Members are notified according to their preferences." actions={<Button onClick={() => open("new")}><Megaphone /> New announcement</Button>} />
      <DataTable
        rows={data?.data}
        loading={isLoading}
        error={error}
        onRetry={() => refetch()}
        page={page}
        totalPages={data?.meta.total_pages}
        onPage={setPage}
        empty="No announcements yet"
        columns={[
          { header: "Title", cell: (a) => <span className="font-semibold text-navy">{a.title}{a.priority === "important" && <span className="ml-2 text-xs font-bold text-red-600">IMPORTANT</span>}</span> },
          { header: "Audience", cell: (a) => a.area_council?.short_name ?? "All members" },
          { header: "Publish", cell: (a) => (a.publish_at ? formatDateTime(a.publish_at) : "Immediately") },
          { header: "Expires", cell: (a) => (a.expires_at ? formatDateTime(a.expires_at) : "—") },
          { header: "Status", cell: (a) => <StatusBadge status={effectiveStatus(a)} /> },
          {
            header: "",
            className: "text-right whitespace-nowrap",
            cell: (a) => (
              <span className="inline-flex gap-1">
                <Button size="sm" variant="ghost" onClick={() => open(a)} aria-label="Edit"><Pencil /></Button>
                {a.status === "draft" && <Button size="sm" variant="ghost" onClick={() => act.mutate({ id: a.id, a: "publish" })}><Send /> Publish</Button>}
                {a.status === "published" && effectiveStatus(a) !== "expired" && <Button size="sm" variant="ghost" onClick={() => act.mutate({ id: a.id, a: "expire" })}><TimerOff /> Expire</Button>}
                <Button size="sm" variant="ghost" className="text-red-600" aria-label="Delete" onClick={async () => { if (await confirm({ title: "Delete announcement?", confirmLabel: "Delete", destructive: true })) { await api.del(`/api/admin/announcements/${a.id}`); invalidate(); } }}><Trash2 /></Button>
              </span>
            ),
          },
        ]}
      />
      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        <DialogContent className="max-w-xl">
          <DialogHeader><DialogTitle>{editing === "new" ? "New announcement" : "Edit announcement"}</DialogTitle></DialogHeader>
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
            <Field id="a-title" label="Title"><Input value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} required minLength={4} /></Field>
            <Field id="a-body" label="Message"><Textarea value={f.body} onChange={(e) => setF({ ...f, body: e.target.value })} maxLength={5000} /></Field>
            <Field id="a-link" label="Link" optional hint="Site path like /events or a full https:// URL"><Input value={f.link_url} onChange={(e) => setF({ ...f, link_url: e.target.value })} /></Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field id="a-aud" label="Audience"><Select value={f.area_council} disabled={!!scoped} onChange={(e) => setF({ ...f, area_council: e.target.value })}><option value="">All members</option>{meta.data?.area_councils.map((c) => <option key={c.slug} value={c.slug}>{c.name} members</option>)}</Select></Field>
              <Field id="a-pri" label="Priority"><Select value={f.priority} onChange={(e) => setF({ ...f, priority: e.target.value })}><option value="normal">Normal</option><option value="important">Important</option></Select></Field>
              <Field id="a-pub" label="Publish at (WAT)" optional hint="Leave empty to publish immediately"><Input type="datetime-local" value={f.publish_at} onChange={(e) => setF({ ...f, publish_at: e.target.value })} /></Field>
              <Field id="a-exp" label="Expires at (WAT)" optional><Input type="datetime-local" value={f.expires_at} onChange={(e) => setF({ ...f, expires_at: e.target.value })} /></Field>
            </div>
            <div className="flex justify-end gap-2"><Button type="button" variant="outline" onClick={() => setEditing(null)}>Cancel</Button><Button type="submit" loading={save.isPending}>Save</Button></div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
