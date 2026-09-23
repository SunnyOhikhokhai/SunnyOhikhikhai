import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, FilePlus2, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { ContentLabelBadge, DemoBadge } from "@/components/shared/badges";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { useConfirm } from "@/components/ui/confirm";
import { Input, Select } from "@/components/ui/input";
import { Field } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { useMeta } from "@/hooks/useMeta";
import { api, getData } from "@/lib/api";
import { CONTENT_LABELS } from "@/lib/constants";
import type { ContentLabel, NewsDetail } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { FormSection, MarkdownEditor, UploadButton } from "./editor-kit";
import { AdminTitle, DataTable, SearchBox, StatusBadge, useAdminList, useSearchState } from "./shared";

function NewsList() {
  const { q, setQ, dq } = useSearchState();
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading, error, refetch } = useAdminList<NewsDetail>("news", "/api/admin/news", { q: dq, status, page });
  return (
    <>
      <AdminTitle title="News" description="Draft, publish and manage articles." actions={<Button asChild><Link to="new"><FilePlus2 /> New article</Link></Button>} />
      <div className="mb-5 flex flex-wrap gap-2">
        <SearchBox value={q} onChange={setQ} placeholder="Search articles" />
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
        empty="No articles yet"
        columns={[
          { header: "Title", cell: (n) => <Link to={String(n.id)} className="font-semibold text-navy hover:text-green-600">{n.title}</Link> },
          { header: "Category", cell: (n) => n.category.name },
          { header: "Label", cell: (n) => <ContentLabelBadge label={n.content_label} /> },
          { header: "Status", cell: (n) => <span className="flex gap-1"><StatusBadge status={n.status ?? "draft"} />{n.is_demo && <DemoBadge />}</span> },
          { header: "Views", cell: (n) => n.view_count ?? 0 },
          { header: "Published", cell: (n) => (n.published_at ? formatDate(n.published_at) : "—") },
        ]}
      />
    </>
  );
}

function NewsEditor() {
  const { id } = useParams();
  const isNew = id === "new";
  const { user } = useAuth();
  const navigate = useNavigate();
  const confirm = useConfirm();
  const qc = useQueryClient();
  const meta = useMeta();
  const scoped = user?.admin?.role === "area_council_admin" ? user.admin.area_council?.slug ?? "" : "";
  const [f, setF] = useState({
    title: "", excerpt: "", body: "", category: "nipam-updates", area_council: scoped, content_label: "update" as ContentLabel,
    source_note: "", image_url: "", image_alt: "", author_name: "NIPAM Editorial Team", is_featured: false, is_demo: false,
  });
  const { data: n, isLoading } = useQuery({ queryKey: ["admin", "news-item", id], queryFn: () => getData<NewsDetail>(`/api/admin/news/${id}`), enabled: !isNew });
  useEffect(() => {
    if (n) setF({ title: n.title, excerpt: n.excerpt, body: n.body, category: n.category.slug, area_council: n.area_council?.slug ?? "", content_label: n.content_label, source_note: n.source_note ?? "", image_url: n.image_url ?? "", image_alt: n.image_alt ?? "", author_name: n.author_name, is_featured: n.is_featured, is_demo: n.is_demo });
  }, [n]);
  const set = <K extends keyof typeof f>(k: K, v: (typeof f)[K]) => setF((x) => ({ ...x, [k]: v }));
  const body = () => ({ ...f, area_council: f.area_council || null, source_note: f.source_note || null, image_url: f.image_url || null, image_alt: f.image_alt || null });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["admin"] });
  const save = useMutation({
    mutationFn: () => (isNew ? api.post<{ data: NewsDetail }>("/api/admin/news", body()) : api.put<{ data: NewsDetail }>(`/api/admin/news/${id}`, body())),
    onSuccess: (r) => { toast.success("Article saved"); invalidate(); if (isNew) navigate(`/admin/news/${r.data.id}`, { replace: true }); },
    onError: (e: Error) => toast.error(e.message),
  });
  const act = useMutation({
    mutationFn: (a: string) => api.post(`/api/admin/news/${id}/${a}`),
    onSuccess: (_, a) => { toast.success(a === "publish" ? "Published — council members notified where applicable" : "Unpublished"); invalidate(); },
    onError: (e: Error) => toast.error(e.message),
  });
  if (!isNew && isLoading) return <Skeleton className="h-96" />;
  return (
    <form onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
      <AdminTitle
        title={isNew ? "New article" : "Edit article"}
        description={n ? `Status: ${n.status}` : "Articles are saved as drafts until published."}
        actions={
          <>
            {n?.status === "published" && <Button asChild variant="ghost"><Link to={`/news/${n.slug}`} target="_blank"><ExternalLink /> View</Link></Button>}
            {!isNew && (n?.status === "published" ? <Button type="button" variant="outline" onClick={() => act.mutate("unpublish")}>Unpublish</Button> : <Button type="button" variant="navy" onClick={() => act.mutate("publish")} loading={act.isPending}>Publish</Button>)}
            <Button type="submit" loading={save.isPending}>Save draft</Button>
          </>
        }
      />
      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <FormSection title="Article">
          <Field id="n-title" label="Title"><Input value={f.title} onChange={(e) => set("title", e.target.value)} required minLength={4} /></Field>
          <Field id="n-excerpt" label="Summary" hint="Shown on cards and in search results."><Input value={f.excerpt} onChange={(e) => set("excerpt", e.target.value)} maxLength={400} /></Field>
          <div className="space-y-1.5"><label htmlFor="n-body" className="text-sm font-semibold text-navy-900">Body</label><MarkdownEditor id="n-body" value={f.body} onChange={(v) => set("body", v)} rows={16} /></div>
        </FormSection>
        <aside className="space-y-6">
          <FormSection title="Classification">
            <Field id="n-cat" label="Category"><Select value={f.category} onChange={(e) => set("category", e.target.value)}>{meta.data?.news_categories.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}</Select></Field>
            <Field id="n-label" label="Content label" hint="Distinguishes verified information from announcements and opinion.">
              <Select value={f.content_label} onChange={(e) => set("content_label", e.target.value as ContentLabel)}>{Object.entries(CONTENT_LABELS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}</Select>
            </Field>
            <Field id="n-source" label="Source" optional={f.content_label !== "verified_information"} hint="e.g. According to … / Published by …"><Input value={f.source_note} onChange={(e) => set("source_note", e.target.value)} required={f.content_label === "verified_information"} /></Field>
            <Field id="n-council" label="Area Council"><Select value={f.area_council} disabled={!!scoped} onChange={(e) => set("area_council", e.target.value)}><option value="">FCT-wide</option>{meta.data?.area_councils.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}</Select></Field>
            <Field id="n-author" label="Author / editor"><Input value={f.author_name} onChange={(e) => set("author_name", e.target.value)} /></Field>
          </FormSection>
          <FormSection title="Featured image">
            {f.image_url && <img src={f.image_url} alt="" className="aspect-video w-full rounded-xl object-cover" />}
            <div className="flex gap-2"><UploadButton folder="news" onUploaded={(url) => set("image_url", url)} label={f.image_url ? "Replace" : "Upload image"} />{f.image_url && <Button type="button" variant="ghost" size="sm" onClick={() => set("image_url", "")}>Remove</Button>}</div>
            {f.image_url && <Field id="n-alt" label="Alt text"><Input value={f.image_alt} onChange={(e) => set("image_alt", e.target.value)} required /></Field>}
          </FormSection>
          <FormSection title="Display">
            <label className="flex items-center gap-3 text-sm"><Checkbox checked={f.is_featured} onCheckedChange={(v) => set("is_featured", v === true)} /> Featured</label>
            <label className="flex items-center gap-3 text-sm"><Checkbox checked={f.is_demo} onCheckedChange={(v) => set("is_demo", v === true)} /> Sample / demo content</label>
          </FormSection>
          {!isNew && (
            <Button type="button" variant="ghost" className="w-full text-red-600 hover:bg-red-50" onClick={async () => {
              if (await confirm({ title: "Delete this article?", confirmLabel: "Delete", destructive: true })) { await api.del(`/api/admin/news/${id}`); invalidate(); toast.success("Deleted"); navigate("/admin/news"); }
            }}><Trash2 /> Delete article</Button>
          )}
        </aside>
      </div>
    </form>
  );
}

export default function NewsAdmin() {
  return (
    <Routes>
      <Route index element={<NewsList />} />
      <Route path=":id" element={<NewsEditor />} />
    </Routes>
  );
}
