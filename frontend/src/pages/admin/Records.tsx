import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, FilePlus2, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { DemoBadge, VerificationBadge } from "@/components/shared/badges";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { useConfirm } from "@/components/ui/confirm";
import { Input, Select } from "@/components/ui/input";
import { Field } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { useMeta } from "@/hooks/useMeta";
import { api, ApiError, getData } from "@/lib/api";
import { VERIFICATION } from "@/lib/constants";
import type { RecordDetail, VerificationStatus } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { FormSection, MarkdownEditor, UploadButton } from "./editor-kit";
import { AdminTitle, DataTable, SearchBox, StatusBadge, useAdminList, useSearchState } from "./shared";

type Src = { title: string; publisher: string; url: string; published_on: string; notes: string };
type Img = { url: string; alt: string; caption: string; credit: string };
type Doc = { title: string; url: string; file_type: string };

const EMPTY = {
  title: "",
  category: "infrastructure",
  area_council: "",
  location: "",
  year: "",
  record_date: "",
  summary: "",
  description: "",
  verification_status: "unverified" as VerificationStatus,
  verification_note: "",
  is_featured: false,
  is_demo: false,
  sources: [] as Src[],
  images: [] as Img[],
  documents: [] as Doc[],
};

function RecordList() {
  const { q, setQ, dq } = useSearchState();
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading, error, refetch } = useAdminList<RecordDetail>("records", "/api/admin/projects", { q: dq, status, page });
  return (
    <>
      <AdminTitle title="Our Record" description="Evidence-oriented records. Every factual claim should cite a source." actions={<Button asChild><Link to="new"><FilePlus2 /> New record</Link></Button>} />
      <div className="mb-5 flex flex-wrap gap-2">
        <SearchBox value={q} onChange={setQ} placeholder="Search records" />
        <Select value={status} onChange={(e) => setStatus(e.target.value)} className="h-10 w-40" aria-label="Status"><option value="">All</option><option value="draft">Drafts</option><option value="published">Published</option></Select>
      </div>
      <DataTable
        rows={data?.data}
        loading={isLoading}
        error={error}
        onRetry={() => refetch()}
        page={page}
        totalPages={data?.meta.total_pages}
        onPage={setPage}
        empty="No records yet"
        columns={[
          { header: "Title", cell: (r) => <Link to={String(r.id)} className="font-semibold text-navy hover:text-green-600">{r.title}</Link> },
          { header: "Council", cell: (r) => r.area_council?.short_name ?? "FCT" },
          { header: "Verification", cell: (r) => <VerificationBadge status={r.verification_status} /> },
          { header: "Sources", cell: (r) => r.sources.length },
          { header: "Status", cell: (r) => <span className="flex gap-1"><StatusBadge status={r.status ?? "draft"} />{r.is_demo && <DemoBadge />}</span> },
          { header: "Updated", cell: (r) => formatDate(r.updated_at) },
        ]}
      />
    </>
  );
}

function RecordEditor() {
  const { id } = useParams();
  const isNew = id === "new";
  const navigate = useNavigate();
  const qc = useQueryClient();
  const confirm = useConfirm();
  const meta = useMeta();
  const { can } = useAuth();
  const [f, setF] = useState(EMPTY);
  const { data: existing, isLoading } = useQuery({ queryKey: ["admin", "record", id], queryFn: () => getData<RecordDetail>(`/api/admin/projects/${id}`), enabled: !isNew });

  useEffect(() => {
    if (!existing) return;
    setF({
      title: existing.title,
      category: existing.category.slug,
      area_council: existing.area_council?.slug ?? "",
      location: existing.location ?? "",
      year: existing.year ? String(existing.year) : "",
      record_date: existing.record_date ?? "",
      summary: existing.summary,
      description: existing.description,
      verification_status: existing.verification_status,
      verification_note: existing.verification_note ?? "",
      is_featured: existing.is_featured,
      is_demo: existing.is_demo,
      sources: existing.sources.map((s) => ({ title: s.title, publisher: s.publisher ?? "", url: s.url ?? "", published_on: s.published_on ?? "", notes: s.notes ?? "" })),
      images: existing.images.map((i) => ({ url: i.url, alt: i.alt, caption: i.caption ?? "", credit: i.credit ?? "" })),
      documents: existing.documents.map((d) => ({ title: d.title, url: d.url, file_type: d.file_type ?? "" })),
    });
  }, [existing]);

  const payload = () => ({
    ...f,
    area_council: f.area_council || null,
    location: f.location || null,
    year: f.year ? Number(f.year) : null,
    record_date: f.record_date || null,
    verification_note: f.verification_note || null,
    sources: f.sources.map((s) => ({ ...s, publisher: s.publisher || null, url: s.url || null, published_on: s.published_on || null, notes: s.notes || null })),
    images: f.images.map((i) => ({ ...i, caption: i.caption || null, credit: i.credit || null })),
    documents: f.documents.map((d) => ({ ...d, file_type: d.file_type || null })),
  });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["admin"] });
  const save = useMutation({
    mutationFn: () => (isNew ? api.post<{ data: RecordDetail }>("/api/admin/projects", payload()) : api.put<{ data: RecordDetail }>(`/api/admin/projects/${id}`, payload())),
    onSuccess: (r) => {
      toast.success("Record saved");
      invalidate();
      if (isNew) navigate(`/admin/records/${r.data.id}`, { replace: true });
    },
    onError: (e: Error) => toast.error(e instanceof ApiError && e.fields ? Object.entries(e.fields).map(([k, v]) => `${k}: ${v}`).join("; ") : e.message),
  });
  const action = useMutation({
    mutationFn: (a: "publish" | "unpublish") => api.post(`/api/admin/projects/${id}/${a}`),
    onSuccess: (_, a) => { toast.success(a === "publish" ? "Record published" : "Record unpublished"); invalidate(); },
    onError: (e: Error) => toast.error(e.message),
  });

  if (!isNew && isLoading) return <Skeleton className="h-96" />;
  const set = <K extends keyof typeof f>(k: K, v: (typeof f)[K]) => setF((x) => ({ ...x, [k]: v }));
  const upd = <T,>(k: "sources" | "images" | "documents", i: number, patch: Partial<T>) =>
    setF((x) => ({ ...x, [k]: (x[k] as T[]).map((item, j) => (j === i ? { ...item, ...patch } : item)) }));
  const del = (k: "sources" | "images" | "documents", i: number) => setF((x) => ({ ...x, [k]: (x[k] as unknown[]).filter((_, j) => j !== i) }));

  return (
    <form onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
      <AdminTitle
        title={isNew ? "New record" : "Edit record"}
        description={existing ? `Status: ${existing.status} · ${existing.view_count} views` : "Records are saved as drafts until published."}
        actions={
          <>
            {!isNew && existing?.status === "published" && <Button asChild variant="ghost"><Link to={`/our-record/${existing.slug}`} target="_blank"><ExternalLink /> View</Link></Button>}
            {!isNew && (existing?.status === "published"
              ? <Button type="button" variant="outline" onClick={() => action.mutate("unpublish")} loading={action.isPending}>Unpublish</Button>
              : <Button type="button" variant="navy" onClick={() => action.mutate("publish")} loading={action.isPending}>Publish</Button>)}
            <Button type="submit" loading={save.isPending}>Save</Button>
          </>
        }
      />
      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          <FormSection title="Record details">
            <Field id="r-title" label="Project / action title"><Input value={f.title} onChange={(e) => set("title", e.target.value)} required minLength={4} /></Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field id="r-cat" label="Category"><Select value={f.category} onChange={(e) => set("category", e.target.value)}>{meta.data?.project_categories.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}</Select></Field>
              <Field id="r-council" label="Area Council"><Select value={f.area_council} onChange={(e) => set("area_council", e.target.value)}><option value="">FCT-wide</option>{meta.data?.area_councils.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}</Select></Field>
              <Field id="r-loc" label="Location" optional><Input value={f.location} onChange={(e) => set("location", e.target.value)} /></Field>
              <div className="grid grid-cols-2 gap-3">
                <Field id="r-year" label="Year" optional><Input type="number" min={1976} max={2100} value={f.year} onChange={(e) => set("year", e.target.value)} /></Field>
                <Field id="r-date" label="Exact date" optional><Input type="date" value={f.record_date} onChange={(e) => set("record_date", e.target.value)} /></Field>
              </div>
            </div>
            <Field id="r-summary" label="Short description" hint="Shown on cards (max 400 characters)."><Input value={f.summary} onChange={(e) => set("summary", e.target.value)} maxLength={400} /></Field>
            <div className="space-y-1.5"><label htmlFor="r-desc" className="text-sm font-semibold text-navy-900">Full description</label><MarkdownEditor id="r-desc" value={f.description} onChange={(v) => set("description", v)} /></div>
          </FormSection>

          <FormSection title="Sources & references" description="Required before a record can be marked Verified. Cite who published the information and when.">
            {f.sources.map((s, i) => (
              <div key={i} className="grid gap-3 rounded-xl bg-surface p-4 sm:grid-cols-2">
                <Field id={`s-t-${i}`} label="Source title"><Input value={s.title} onChange={(e) => upd<Src>("sources", i, { title: e.target.value })} required /></Field>
                <Field id={`s-p-${i}`} label="Published by" optional><Input value={s.publisher} onChange={(e) => upd<Src>("sources", i, { publisher: e.target.value })} /></Field>
                <Field id={`s-u-${i}`} label="URL" optional><Input type="url" value={s.url} onChange={(e) => upd<Src>("sources", i, { url: e.target.value })} placeholder="https://" /></Field>
                <Field id={`s-d-${i}`} label="Date published" optional><Input type="date" value={s.published_on} onChange={(e) => upd<Src>("sources", i, { published_on: e.target.value })} /></Field>
                <Field id={`s-n-${i}`} label="Notes" optional className="sm:col-span-2"><Input value={s.notes} onChange={(e) => upd<Src>("sources", i, { notes: e.target.value })} /></Field>
                <div className="sm:col-span-2"><Button type="button" size="sm" variant="ghost" className="text-red-600" onClick={() => del("sources", i)}><Trash2 /> Remove source</Button></div>
              </div>
            ))}
            <Button type="button" variant="outline" size="sm" onClick={() => set("sources", [...f.sources, { title: "", publisher: "", url: "", published_on: "", notes: "" }])}><Plus /> Add source</Button>
          </FormSection>

          <FormSection title="Images" description="Upload JPEG, PNG or WebP (max 5 MB). Alt text is required for accessibility.">
            {f.images.map((img, i) => (
              <div key={i} className="grid gap-3 rounded-xl bg-surface p-4 sm:grid-cols-[120px_1fr]">
                <img src={img.url} alt="" className="aspect-square w-full rounded-lg object-cover" />
                <div className="grid gap-3 sm:grid-cols-2">
                  <Field id={`i-a-${i}`} label="Alt text" className="sm:col-span-2"><Input value={img.alt} onChange={(e) => upd<Img>("images", i, { alt: e.target.value })} required /></Field>
                  <Field id={`i-c-${i}`} label="Caption" optional><Input value={img.caption} onChange={(e) => upd<Img>("images", i, { caption: e.target.value })} /></Field>
                  <Field id={`i-cr-${i}`} label="Photo credit" optional><Input value={img.credit} onChange={(e) => upd<Img>("images", i, { credit: e.target.value })} /></Field>
                  <div><Button type="button" size="sm" variant="ghost" className="text-red-600" onClick={() => del("images", i)}><Trash2 /> Remove</Button></div>
                </div>
              </div>
            ))}
            <UploadButton folder="records" label="Upload image" onUploaded={(url) => set("images", [...f.images, { url, alt: "", caption: "", credit: "" }])} />
          </FormSection>

          <FormSection title="Supporting documents" description="PDF documents (max 5 MB).">
            {f.documents.map((d, i) => (
              <div key={i} className="flex flex-wrap items-end gap-3 rounded-xl bg-surface p-4">
                <Field id={`d-t-${i}`} label="Document title" className="flex-1"><Input value={d.title} onChange={(e) => upd<Doc>("documents", i, { title: e.target.value })} required /></Field>
                <a href={d.url} target="_blank" rel="noreferrer" className="pb-3 text-sm font-semibold text-green-600">Open</a>
                <Button type="button" size="sm" variant="ghost" className="text-red-600" onClick={() => del("documents", i)}><Trash2 /></Button>
              </div>
            ))}
            <UploadButton folder="documents" accept="application/pdf" label="Upload PDF" onUploaded={(url) => set("documents", [...f.documents, { title: "", url, file_type: "pdf" }])} />
          </FormSection>
        </div>

        <aside className="space-y-6">
          <FormSection title="Verification" description={can("records.verify") ? undefined : "Your role cannot change verification status."}>
            <Field id="r-ver" label="Status">
              <Select value={f.verification_status} disabled={!can("records.verify")} onChange={(e) => set("verification_status", e.target.value as VerificationStatus)}>
                {Object.entries(VERIFICATION).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
              </Select>
            </Field>
            <p className="text-xs text-muted-foreground">{VERIFICATION[f.verification_status].description}</p>
            <Field id="r-vnote" label="Verification note" optional><Input value={f.verification_note} onChange={(e) => set("verification_note", e.target.value)} /></Field>
            {f.verification_status === "verified" && !f.sources.length && <p className="text-sm font-medium text-red-600">Add at least one source to mark this record verified.</p>}
          </FormSection>
          <FormSection title="Display">
            <label className="flex items-start gap-3 text-sm"><Checkbox checked={f.is_featured} onCheckedChange={(v) => set("is_featured", v === true)} /> <span><strong className="text-navy">Featured</strong><br /><span className="text-muted-foreground">Show in the homepage carousel.</span></span></label>
            <label className="flex items-start gap-3 text-sm"><Checkbox checked={f.is_demo} onCheckedChange={(v) => set("is_demo", v === true)} /> <span><strong className="text-navy">Sample / demo content</strong><br /><span className="text-muted-foreground">Displays a "Sample" badge. Untick once real, verified details are added.</span></span></label>
          </FormSection>
          {!isNew && (
            <Button
              type="button"
              variant="ghost"
              className="w-full text-red-600 hover:bg-red-50"
              onClick={async () => {
                if (await confirm({ title: "Delete this record?", description: "It will be removed from the public library.", confirmLabel: "Delete", destructive: true })) {
                  await api.del(`/api/admin/projects/${id}`);
                  toast.success("Record deleted");
                  invalidate();
                  navigate("/admin/records");
                }
              }}
            >
              <Trash2 /> Delete record
            </Button>
          )}
        </aside>
      </div>
    </form>
  );
}

export default function Records() {
  return (
    <Routes>
      <Route index element={<RecordList />} />
      <Route path=":id" element={<RecordEditor />} />
    </Routes>
  );
}
