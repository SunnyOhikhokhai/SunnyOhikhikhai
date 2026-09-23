import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, CalendarPlus, ExternalLink, Send, Trash2, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { DemoBadge } from "@/components/shared/badges";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { useConfirm } from "@/components/ui/confirm";
import { Input, Select } from "@/components/ui/input";
import { Field } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { useMeta } from "@/hooks/useMeta";
import { api, getData } from "@/lib/api";
import type { EventItem } from "@/lib/types";
import { formatDateTime, fromLocalInput, toLocalInput } from "@/lib/utils";
import { FormSection, MarkdownEditor, UploadButton } from "./editor-kit";
import { AdminTitle, DataTable, SearchBox, StatusBadge, useAdminList, useSearchState } from "./shared";

function EventList() {
  const { q, setQ, dq } = useSearchState();
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading, error, refetch } = useAdminList<EventItem>("events", "/api/admin/events", { q: dq, status, page });
  return (
    <>
      <AdminTitle title="Events" description="Create, publish, cancel and archive events." actions={<Button asChild><Link to="new"><CalendarPlus /> New event</Link></Button>} />
      <div className="mb-5 flex flex-wrap gap-2">
        <SearchBox value={q} onChange={setQ} placeholder="Search events" />
        <Select value={status} onChange={(e) => setStatus(e.target.value)} className="h-10 w-40" aria-label="Status">
          <option value="">All</option>{["draft", "published", "cancelled", "archived"].map((s) => <option key={s} value={s} className="capitalize">{s}</option>)}
        </Select>
      </div>
      <DataTable
        rows={data?.data}
        loading={isLoading}
        error={error}
        onRetry={() => refetch()}
        page={page}
        totalPages={data?.meta.total_pages}
        onPage={setPage}
        empty="No events yet"
        columns={[
          { header: "Event", cell: (e) => <Link to={String(e.id)} className="font-semibold text-navy hover:text-green-600">{e.title}</Link> },
          { header: "When", cell: (e) => formatDateTime(e.starts_at) },
          { header: "Council", cell: (e) => e.area_council?.short_name ?? "FCT" },
          { header: "Registered", cell: (e) => `${e.registered_count ?? 0}${e.capacity ? ` / ${e.capacity}` : ""}` },
          { header: "Status", cell: (e) => <span className="flex gap-1"><StatusBadge status={e.status} />{e.is_demo && <DemoBadge />}</span> },
        ]}
      />
    </>
  );
}

function EventEditor() {
  const { id } = useParams();
  const isNew = id === "new";
  const { user } = useAuth();
  const scoped = user?.admin?.role === "area_council_admin" ? user.admin.area_council?.slug ?? "" : "";
  const navigate = useNavigate();
  const confirm = useConfirm();
  const qc = useQueryClient();
  const meta = useMeta();
  const [f, setF] = useState({ title: "", summary: "", description: "", starts_at: "", ends_at: "", location: "", area_council: scoped, image_url: "", organizer: "NIPAM", registration_open: true, capacity: "", is_demo: false });
  const { data: e, isLoading } = useQuery({ queryKey: ["admin", "event", id], queryFn: () => getData<EventItem>(`/api/admin/events/${id}`), enabled: !isNew });
  useEffect(() => {
    if (e) setF({ title: e.title, summary: e.summary, description: e.description ?? "", starts_at: toLocalInput(e.starts_at), ends_at: toLocalInput(e.ends_at), location: e.location, area_council: e.area_council?.slug ?? "", image_url: e.image_url ?? "", organizer: e.organizer, registration_open: e.registration_open, capacity: e.capacity ? String(e.capacity) : "", is_demo: e.is_demo });
  }, [e]);
  const set = <K extends keyof typeof f>(k: K, v: (typeof f)[K]) => setF((x) => ({ ...x, [k]: v }));
  const body = () => ({ ...f, starts_at: fromLocalInput(f.starts_at), ends_at: fromLocalInput(f.ends_at), area_council: f.area_council || null, image_url: f.image_url || null, capacity: f.capacity ? Number(f.capacity) : null });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["admin"] });
  const save = useMutation({
    mutationFn: () => (isNew ? api.post<{ data: EventItem }>("/api/admin/events", body()) : api.put<{ data: EventItem }>(`/api/admin/events/${id}`, body())),
    onSuccess: (r) => { toast.success("Event saved"); invalidate(); if (isNew) navigate(`/admin/events/${r.data.id}`, { replace: true }); },
    onError: (err: Error) => toast.error(err.message),
  });
  const status = useMutation({
    mutationFn: (s: string) => api.post(`/api/admin/events/${id}/status?status=${s}`),
    onSuccess: (_, s) => { toast.success(s === "published" ? "Published — members notified" : s === "cancelled" ? "Cancelled — registrants notified" : `Event ${s}`); invalidate(); },
    onError: (err: Error) => toast.error(err.message),
  });
  if (!isNew && isLoading) return <Skeleton className="h-96" />;
  return (
    <form onSubmit={(ev) => { ev.preventDefault(); save.mutate(); }}>
      <AdminTitle
        title={isNew ? "New event" : "Edit event"}
        description={e ? `Status: ${e.status} · ${e.registered_count ?? 0} registered · ${e.view_count ?? 0} views` : "All times are West Africa Time (WAT)."}
        actions={
          <>
            {e && e.status !== "draft" && <Button asChild variant="ghost"><Link to={`/events/${e.slug}`} target="_blank"><ExternalLink /> View</Link></Button>}
            {e?.status === "draft" && <Button type="button" variant="navy" onClick={() => status.mutate("published")} loading={status.isPending}><Send /> Publish</Button>}
            {e?.status === "published" && (
              <Button type="button" variant="outline" className="text-red-600" onClick={async () => { if (await confirm({ title: "Cancel this event?", description: "Registered members will be notified.", confirmLabel: "Cancel event", destructive: true })) status.mutate("cancelled"); }}>
                <XCircle /> Cancel event
              </Button>
            )}
            {e && e.status !== "archived" && e.status !== "draft" && <Button type="button" variant="outline" onClick={() => status.mutate("archived")}><Archive /> Archive</Button>}
            <Button type="submit" loading={save.isPending}>Save</Button>
          </>
        }
      />
      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <FormSection title="Event details">
          <Field id="e-title" label="Event title"><Input value={f.title} onChange={(ev) => set("title", ev.target.value)} required minLength={4} /></Field>
          <Field id="e-summary" label="Summary"><Input value={f.summary} onChange={(ev) => set("summary", ev.target.value)} maxLength={400} /></Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field id="e-start" label="Starts (WAT)"><Input type="datetime-local" value={f.starts_at} onChange={(ev) => set("starts_at", ev.target.value)} required /></Field>
            <Field id="e-end" label="Ends (WAT)" optional><Input type="datetime-local" value={f.ends_at} onChange={(ev) => set("ends_at", ev.target.value)} /></Field>
            <Field id="e-loc" label="Location"><Input value={f.location} onChange={(ev) => set("location", ev.target.value)} required /></Field>
            <Field id="e-council" label="Area Council"><Select value={f.area_council} disabled={!!scoped} onChange={(ev) => set("area_council", ev.target.value)}><option value="">FCT-wide</option>{meta.data?.area_councils.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}</Select></Field>
            <Field id="e-org" label="Organiser"><Input value={f.organizer} onChange={(ev) => set("organizer", ev.target.value)} /></Field>
          </div>
          <div className="space-y-1.5"><label htmlFor="e-desc" className="text-sm font-semibold text-navy-900">Description</label><MarkdownEditor id="e-desc" value={f.description} onChange={(v) => set("description", v)} /></div>
        </FormSection>
        <aside className="space-y-6">
          <FormSection title="Registration">
            <label className="flex items-center gap-3 text-sm"><Checkbox checked={f.registration_open} onCheckedChange={(v) => set("registration_open", v === true)} /> Registration open</label>
            <Field id="e-cap" label="Capacity" optional><Input type="number" min={1} value={f.capacity} onChange={(ev) => set("capacity", ev.target.value)} /></Field>
          </FormSection>
          <FormSection title="Image">
            {f.image_url && <img src={f.image_url} alt="" className="aspect-video w-full rounded-xl object-cover" />}
            <UploadButton folder="events" onUploaded={(url) => set("image_url", url)} label={f.image_url ? "Replace image" : "Upload image"} />
            <label className="flex items-center gap-3 text-sm"><Checkbox checked={f.is_demo} onCheckedChange={(v) => set("is_demo", v === true)} /> Sample / demo content</label>
          </FormSection>
          {!isNew && (
            <Button type="button" variant="ghost" className="w-full text-red-600 hover:bg-red-50" onClick={async () => {
              if (await confirm({ title: "Delete this event?", confirmLabel: "Delete", destructive: true })) { await api.del(`/api/admin/events/${id}`); invalidate(); navigate("/admin/events"); }
            }}><Trash2 /> Delete event</Button>
          )}
        </aside>
      </div>
    </form>
  );
}

export default function EventsAdmin() {
  return (
    <Routes>
      <Route index element={<EventList />} />
      <Route path=":id" element={<EventEditor />} />
    </Routes>
  );
}
