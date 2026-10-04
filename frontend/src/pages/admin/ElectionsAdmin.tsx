import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, FilePlus2, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { VerificationBadge } from "@/components/shared/badges";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { useConfirm } from "@/components/ui/confirm";
import { Input, Textarea } from "@/components/ui/input";
import { Field } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { api, getData } from "@/lib/api";
import type { ElectionRecord, VerificationStatus } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { FormSection, LinkedSourcesEditor, VerificationSelect, linkedPayload, toLinked, type LinkedSrc } from "./editor-kit";
import { errorText } from "./LegislationAdmin";
import { AdminTitle, DataTable, StatusBadge, useAdminList } from "./shared";

const EMPTY = {
  year: "",
  title: "",
  constituency: "Federal Capital Territory",
  candidate: "",
  party: "",
  outcome: "",
  votes: "",
  votes_note: "",
  election_date: "",
  summary: "",
  verification_status: "pending" as VerificationStatus,
  verification_note: "",
  is_current: false,
  sources: [] as LinkedSrc[],
};

function List() {
  const [page, setPage] = useState(1);
  const { data, isLoading, error, refetch } = useAdminList<ElectionRecord>("elections", "/api/admin/elections", { page });
  return (
    <>
      <AdminTitle
        title="Elections"
        description="Election records. Use INEC as the authoritative source for candidacy and results."
        actions={<Button asChild><Link to="new"><FilePlus2 /> New election record</Link></Button>}
      />
      <DataTable
        rows={data?.data}
        loading={isLoading}
        error={error}
        onRetry={() => refetch()}
        page={page}
        totalPages={data?.meta.total_pages}
        onPage={setPage}
        empty="No election records yet"
        columns={[
          { header: "Year", cell: (r) => r.year },
          { header: "Title", cell: (r) => <Link to={String(r.id)} className="font-semibold text-navy hover:text-green-600">{r.title}</Link> },
          { header: "Party", cell: (r) => r.party },
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
    queryKey: ["admin", "election", id],
    queryFn: () => getData<ElectionRecord>(`/api/admin/elections/${id}`),
    enabled: !isNew,
  });
  useEffect(() => {
    if (!existing) return;
    setF({
      year: String(existing.year),
      title: existing.title,
      constituency: existing.constituency,
      candidate: existing.candidate,
      party: existing.party,
      outcome: existing.outcome,
      votes: existing.votes != null ? String(existing.votes) : "",
      votes_note: existing.votes_note ?? "",
      election_date: existing.election_date ?? "",
      summary: existing.summary,
      verification_status: existing.verification_status,
      verification_note: existing.verification_note ?? "",
      is_current: existing.is_current,
      sources: existing.sources.map(toLinked),
    });
  }, [existing]);
  const set = <K extends keyof typeof f>(k: K, v: (typeof f)[K]) => setF((x) => ({ ...x, [k]: v }));
  const payload = () => ({
    ...f,
    year: Number(f.year),
    votes: f.votes ? Number(f.votes) : null,
    votes_note: f.votes_note || null,
    election_date: f.election_date || null,
    verification_note: f.verification_note || null,
    sources: linkedPayload(f.sources),
  });
  const invalidate = () => qc.invalidateQueries({ queryKey: ["admin"] });
  const save = useMutation({
    mutationFn: () =>
      isNew ? api.post<{ data: ElectionRecord }>("/api/admin/elections", payload()) : api.put<{ data: ElectionRecord }>(`/api/admin/elections/${id}`, payload()),
    onSuccess: (r) => {
      toast.success("Election record saved");
      invalidate();
      if (isNew) navigate(`/admin/elections/${r.data.id}`, { replace: true });
    },
    onError: (e: Error) => toast.error(errorText(e)),
  });
  const action = useMutation({
    mutationFn: (a: "publish" | "unpublish") => api.post(`/api/admin/elections/${id}/${a}`),
    onSuccess: (_, a) => { toast.success(a === "publish" ? "Published" : "Unpublished"); invalidate(); },
    onError: (e: Error) => toast.error(e.message),
  });
  if (!isNew && isLoading) return <Skeleton className="h-96" />;

  return (
    <form onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
      <AdminTitle
        title={isNew ? "New election record" : "Edit election record"}
        description={existing ? `Status: ${existing.status}` : "Saved as a draft until published."}
        actions={
          <>
            {!isNew && existing?.status === "published" && <Button asChild variant="ghost"><Link to="/elections" target="_blank"><ExternalLink /> View</Link></Button>}
            {!isNew && (existing?.status === "published"
              ? <Button type="button" variant="outline" onClick={() => action.mutate("unpublish")} loading={action.isPending}>Unpublish</Button>
              : <Button type="button" variant="navy" onClick={() => action.mutate("publish")} loading={action.isPending}>Publish</Button>)}
            <Button type="submit" loading={save.isPending}>Save</Button>
          </>
        }
      />
      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          <FormSection title="Election details">
            <div className="grid gap-4 sm:grid-cols-[120px_1fr]">
              <Field id="e-year" label="Year"><Input type="number" min={1976} max={2100} value={f.year} onChange={(e) => set("year", e.target.value)} required /></Field>
              <Field id="e-title" label="Title"><Input value={f.title} onChange={(e) => set("title", e.target.value)} required minLength={4} /></Field>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <Field id="e-cand" label="Candidate"><Input value={f.candidate} onChange={(e) => set("candidate", e.target.value)} /></Field>
              <Field id="e-party" label="Party"><Input value={f.party} onChange={(e) => set("party", e.target.value)} maxLength={40} /></Field>
              <Field id="e-const" label="Constituency"><Input value={f.constituency} onChange={(e) => set("constituency", e.target.value)} /></Field>
            </div>
            <Field id="e-out" label="Outcome" hint="As stated by the source."><Input value={f.outcome} onChange={(e) => set("outcome", e.target.value)} maxLength={300} /></Field>
            <div className="grid gap-4 sm:grid-cols-3">
              <Field id="e-date" label="Election date" optional><Input type="date" value={f.election_date} onChange={(e) => set("election_date", e.target.value)} /></Field>
              <Field id="e-votes" label="Votes" optional><Input type="number" min={0} value={f.votes} onChange={(e) => set("votes", e.target.value)} /></Field>
              <Field id="e-vnote" label="Where the vote total comes from" optional><Input value={f.votes_note} onChange={(e) => set("votes_note", e.target.value)} maxLength={300} /></Field>
            </div>
            <Field id="e-sum" label="Summary"><Textarea value={f.summary} onChange={(e) => set("summary", e.target.value)} maxLength={5000} /></Field>
          </FormSection>
          <FormSection title="Sources" description="INEC documents are the authoritative source.">
            <LinkedSourcesEditor value={f.sources} onChange={(v) => set("sources", v)} />
          </FormSection>
        </div>
        <aside className="space-y-6">
          <FormSection title="Verification" description={can("records.verify") ? undefined : "Your role cannot change verification status."}>
            <VerificationSelect id="e-ver" value={f.verification_status} onChange={(v) => set("verification_status", v)} disabled={!can("records.verify")} />
            <Field id="e-vn" label="Verification note" optional><Input value={f.verification_note} onChange={(e) => set("verification_note", e.target.value)} maxLength={500} /></Field>
            {f.verification_status === "verified" && !f.sources.length && <p className="text-sm font-medium text-red-600">Add at least one source to mark this record verified.</p>}
          </FormSection>
          <FormSection title="Display">
            <label className="flex items-start gap-3 text-sm"><Checkbox checked={f.is_current} onCheckedChange={(v) => set("is_current", v === true)} /> <span><strong className="text-navy">Current election</strong><br /><span className="text-muted-foreground">Shown on the homepage and profile page.</span></span></label>
          </FormSection>
          {!isNew && (
            <Button
              type="button"
              variant="ghost"
              className="w-full text-red-600 hover:bg-red-50"
              onClick={async () => {
                if (await confirm({ title: "Delete this election record?", description: "It will be removed from the public site.", confirmLabel: "Delete", destructive: true })) {
                  await api.del(`/api/admin/elections/${id}`);
                  toast.success("Deleted");
                  invalidate();
                  navigate("/admin/elections");
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

export default function ElectionsAdmin() {
  return (
    <Routes>
      <Route index element={<List />} />
      <Route path=":id" element={<Editor />} />
    </Routes>
  );
}
