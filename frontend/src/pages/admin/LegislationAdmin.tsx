import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, FilePlus2, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { StageBadge, VerificationBadge } from "@/components/shared/badges";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { useConfirm } from "@/components/ui/confirm";
import { Input, Select, Textarea } from "@/components/ui/input";
import { Field } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError, getData } from "@/lib/api";
import { LEGISLATIVE_STAGES } from "@/lib/constants";
import type { LegislationRecord, LegislativeStage, VerificationStatus } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { FormSection, LinkedSourcesEditor, VerificationSelect, linkedPayload, toLinked, type LinkedSrc } from "./editor-kit";
import { AdminTitle, DataTable, SearchBox, StatusBadge, useAdminList, useSearchState } from "./shared";

const EMPTY = {
  title: "",
  bill_number: "",
  category: "",
  year: "",
  sponsor: "Senator Philip Tanimu Aduda",
  description: "",
  legislative_stage: "pending" as LegislativeStage,
  official_status: "",
  verification_status: "pending" as VerificationStatus,
  verification_note: "",
  is_featured: false,
  sources: [] as LinkedSrc[],
};

export const errorText = (e: Error) =>
  e instanceof ApiError && e.fields ? Object.entries(e.fields).map(([k, v]) => `${k}: ${v}`).join("; ") : e.message;

function List() {
  const { q, setQ, dq } = useSearchState();
  const [page, setPage] = useState(1);
  const { data, isLoading, error, refetch } = useAdminList<LegislationRecord>("legislation", "/api/admin/legislation", { q: dq, page });
  return (
    <>
      <AdminTitle
        title="Legislation"
        description="One record per bill. Record the stage the source documents — never collapse stages into “Passed”."
        actions={<Button asChild><Link to="new"><FilePlus2 /> New legislative record</Link></Button>}
      />
      <div className="mb-5"><SearchBox value={q} onChange={setQ} placeholder="Search bills" /></div>
      <DataTable
        rows={data?.data}
        loading={isLoading}
        error={error}
        onRetry={() => refetch()}
        page={page}
        totalPages={data?.meta.total_pages}
        onPage={setPage}
        empty="No legislative records yet"
        columns={[
          { header: "Title", cell: (r) => <Link to={String(r.id)} className="font-semibold text-navy hover:text-green-600">{r.title}</Link> },
          { header: "Bill", cell: (r) => r.bill_number ?? "—" },
          { header: "Stage", cell: (r) => <StageBadge stage={r.legislative_stage} /> },
          { header: "Verification", cell: (r) => <VerificationBadge status={r.verification_status} /> },
          { header: "Status", cell: (r) => <StatusBadge status={r.status ?? "draft"} /> },
          { header: "Updated", cell: (r) => formatDate(r.updated_at) },
        ]}
      />
    </>
  );
}

function Editor() {
  const { id } = useParams();
  const isNew = id === "new";
  const navigate = useNavigate();
  const qc = useQueryClient();
  const confirm = useConfirm();
  const { can } = useAuth();
  const [f, setF] = useState(EMPTY);
  const { data: existing, isLoading } = useQuery({
    queryKey: ["admin", "legislation", id],
    queryFn: () => getData<LegislationRecord>(`/api/admin/legislation/${id}`),
    enabled: !isNew,
  });
  useEffect(() => {
    if (!existing) return;
    setF({
      title: existing.title,
      bill_number: existing.bill_number ?? "",
      category: existing.category,
      year: existing.year ? String(existing.year) : "",
      sponsor: existing.sponsor,
      description: existing.description,
      legislative_stage: existing.legislative_stage,
      official_status: existing.official_status ?? "",
      verification_status: existing.verification_status,
      verification_note: existing.verification_note ?? "",
      is_featured: existing.is_featured,
      sources: existing.sources.map(toLinked),
    });
  }, [existing]);
  const set = <K extends keyof typeof f>(k: K, v: (typeof f)[K]) => setF((x) => ({ ...x, [k]: v }));
  const payload = () => ({
    ...f,
    bill_number: f.bill_number || null,
    year: f.year ? Number(f.year) : null,
    official_status: f.official_status || null,
    verification_note: f.verification_note || null,
    sources: linkedPayload(f.sources),
  });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["admin"] });
  const save = useMutation({
    mutationFn: () =>
      isNew
        ? api.post<{ data: LegislationRecord }>("/api/admin/legislation", payload())
        : api.put<{ data: LegislationRecord }>(`/api/admin/legislation/${id}`, payload()),
    onSuccess: (r) => {
      toast.success("Legislative record saved");
      invalidate();
      if (isNew) navigate(`/admin/legislation/${r.data.id}`, { replace: true });
    },
    onError: (e: Error) => toast.error(errorText(e)),
  });
  const action = useMutation({
    mutationFn: (a: "publish" | "unpublish") => api.post(`/api/admin/legislation/${id}/${a}`),
    onSuccess: (_, a) => { toast.success(a === "publish" ? "Published" : "Unpublished"); invalidate(); },
    onError: (e: Error) => toast.error(e.message),
  });
  if (!isNew && isLoading) return <Skeleton className="h-96" />;

  return (
    <form onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
      <AdminTitle
        title={isNew ? "New legislative record" : "Edit legislative record"}
        description={existing ? `Status: ${existing.status}` : "Saved as a draft until published."}
        actions={
          <>
            {!isNew && existing?.status === "published" && <Button asChild variant="ghost"><Link to={`/legislation/${existing.slug}`} target="_blank"><ExternalLink /> View</Link></Button>}
            {!isNew && (existing?.status === "published"
              ? <Button type="button" variant="outline" onClick={() => action.mutate("unpublish")} loading={action.isPending}>Unpublish</Button>
              : <Button type="button" variant="navy" onClick={() => action.mutate("publish")} loading={action.isPending}>Publish</Button>)}
            <Button type="submit" loading={save.isPending}>Save</Button>
          </>
        }
      />
      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          <FormSection title="Bill details">
            <Field id="l-title" label="Title"><Input value={f.title} onChange={(e) => set("title", e.target.value)} required minLength={4} /></Field>
            <div className="grid gap-4 sm:grid-cols-3">
              <Field id="l-bill" label="Bill number" optional hint="e.g. SB 668"><Input value={f.bill_number} onChange={(e) => set("bill_number", e.target.value)} maxLength={40} /></Field>
              <Field id="l-cat" label="Category" hint="e.g. Health, Governance"><Input value={f.category} onChange={(e) => set("category", e.target.value)} required minLength={2} maxLength={80} /></Field>
              <Field id="l-year" label="Year" optional><Input type="number" min={1976} max={2100} value={f.year} onChange={(e) => set("year", e.target.value)} /></Field>
            </div>
            <Field id="l-sponsor" label="Sponsor" optional><Input value={f.sponsor} onChange={(e) => set("sponsor", e.target.value)} maxLength={160} /></Field>
            <Field id="l-desc" label="Description"><Textarea value={f.description} onChange={(e) => set("description", e.target.value)} maxLength={20000} /></Field>
          </FormSection>
          <FormSection title="Sources" description="Required before the record can be marked Verified. Sources are shared with the registry, so each URL is stored once.">
            <LinkedSourcesEditor value={f.sources} onChange={(v) => set("sources", v)} />
          </FormSection>
        </div>
        <aside className="space-y-6">
          <FormSection title="Legislative stage" description="Use “Assented / enacted” only with an official enactment or assent record.">
            <Field id="l-stage" label="Stage">
              <Select value={f.legislative_stage} onChange={(e) => set("legislative_stage", e.target.value as LegislativeStage)}>
                {(Object.keys(LEGISLATIVE_STAGES) as LegislativeStage[]).map((k) => <option key={k} value={k}>{LEGISLATIVE_STAGES[k].label}</option>)}
              </Select>
            </Field>
            <p className="text-xs text-muted-foreground">{LEGISLATIVE_STAGES[f.legislative_stage].description}</p>
            <Field id="l-off" label="Status in the source's words" optional hint='e.g. Official-site status: "Passed."'><Input value={f.official_status} onChange={(e) => set("official_status", e.target.value)} maxLength={300} /></Field>
          </FormSection>
          <FormSection title="Verification" description={can("records.verify") ? undefined : "Your role cannot change verification status."}>
            <VerificationSelect id="l-ver" value={f.verification_status} onChange={(v) => set("verification_status", v)} disabled={!can("records.verify")} />
            <Field id="l-vnote" label="Verification note" optional><Input value={f.verification_note} onChange={(e) => set("verification_note", e.target.value)} maxLength={500} /></Field>
            {f.verification_status === "verified" && !f.sources.length && <p className="text-sm font-medium text-red-600">Add at least one source to mark this record verified.</p>}
            {existing?.last_verified_at && <p className="text-xs text-muted-foreground">Last verified {formatDate(existing.last_verified_at)}</p>}
          </FormSection>
          <FormSection title="Display">
            <label className="flex items-start gap-3 text-sm"><Checkbox checked={f.is_featured} onCheckedChange={(v) => set("is_featured", v === true)} /> <span><strong className="text-navy">Featured</strong><br /><span className="text-muted-foreground">Listed first on the Legislation page.</span></span></label>
          </FormSection>
          {!isNew && (
            <Button
              type="button"
              variant="ghost"
              className="w-full text-red-600 hover:bg-red-50"
              onClick={async () => {
                if (await confirm({ title: "Delete this legislative record?", description: "It will be removed from the public site.", confirmLabel: "Delete", destructive: true })) {
                  await api.del(`/api/admin/legislation/${id}`);
                  toast.success("Deleted");
                  invalidate();
                  navigate("/admin/legislation");
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

export default function LegislationAdmin() {
  return (
    <Routes>
      <Route index element={<List />} />
      <Route path=":id" element={<Editor />} />
    </Routes>
  );
}
