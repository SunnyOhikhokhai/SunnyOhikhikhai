import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useConfirm } from "@/components/ui/confirm";
import { Input, Select, Textarea } from "@/components/ui/input";
import { Field } from "@/components/ui/label";
import { api } from "@/lib/api";
import { RELIABILITY, SOURCE_TYPES } from "@/lib/constants";
import type { RegistrySource } from "@/lib/types";
import { FormSection } from "./editor-kit";
import { errorText } from "./LegislationAdmin";
import { AdminTitle, DataTable, SearchBox, useAdminList, useSearchState } from "./shared";

type Form = {
  name: string;
  title: string;
  source_type: string;
  url: string;
  publication_date: string;
  accessed_date: string;
  reliability_level: string;
  notes: string;
};

const EMPTY: Form = { name: "", title: "", source_type: "news", url: "", publication_date: "", accessed_date: "", reliability_level: "news", notes: "" };

const toForm = (s: RegistrySource): Form => ({
  name: s.name,
  title: s.title ?? "",
  source_type: s.source_type,
  url: s.url ?? "",
  publication_date: s.publication_date ?? "",
  accessed_date: s.accessed_date ?? "",
  reliability_level: s.reliability_level,
  notes: s.notes ?? "",
});

export default function SourcesAdmin() {
  const { q, setQ, dq } = useSearchState();
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<number | "new" | null>(null);
  const [f, setF] = useState<Form>(EMPTY);
  const qc = useQueryClient();
  const confirm = useConfirm();
  const { data, isLoading, error, refetch } = useAdminList<RegistrySource>("sources", "/api/admin/sources", { q: dq, page });
  const set = <K extends keyof Form>(k: K, v: Form[K]) => setF((x) => ({ ...x, [k]: v }));
  const payload = () =>
    Object.fromEntries(Object.entries(f).map(([k, v]) => [k, v === "" && k !== "name" ? null : v]));
  const save = useMutation({
    mutationFn: () => (editing === "new" ? api.post("/api/admin/sources", payload()) : api.put(`/api/admin/sources/${editing}`, payload())),
    onSuccess: () => {
      toast.success("Source saved");
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["admin"] });
    },
    onError: (e: Error) => toast.error(errorText(e)),
  });

  const editor = editing !== null && (
    <form onSubmit={(e) => { e.preventDefault(); save.mutate(); }} className="mb-6">
      <FormSection title={editing === "new" ? "New source" : "Edit source"} description="Each URL can appear in the registry only once. Changes apply everywhere the source is cited.">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field id="src-name" label="Source name" hint="Publisher or institution"><Input value={f.name} onChange={(e) => set("name", e.target.value)} required minLength={2} /></Field>
          <Field id="src-title" label="Document / article title" optional><Input value={f.title} onChange={(e) => set("title", e.target.value)} /></Field>
          <Field id="src-url" label="URL" optional className="sm:col-span-2"><Input type="url" value={f.url} onChange={(e) => set("url", e.target.value)} placeholder="https://" /></Field>
          <Field id="src-type" label="Source type">
            <Select value={f.source_type} onChange={(e) => set("source_type", e.target.value)}>
              {Object.entries(SOURCE_TYPES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </Select>
          </Field>
          <Field id="src-rel" label="Reliability level">
            <Select value={f.reliability_level} onChange={(e) => set("reliability_level", e.target.value)}>
              {Object.entries(RELIABILITY).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </Select>
          </Field>
          <Field id="src-pub" label="Publication date" optional><Input type="date" value={f.publication_date} onChange={(e) => set("publication_date", e.target.value)} /></Field>
          <Field id="src-acc" label="Date accessed" optional><Input type="date" value={f.accessed_date} onChange={(e) => set("accessed_date", e.target.value)} /></Field>
          <Field id="src-notes" label="Notes" optional className="sm:col-span-2"><Textarea value={f.notes} onChange={(e) => set("notes", e.target.value)} maxLength={1000} className="min-h-[70px]" /></Field>
        </div>
        <div className="flex gap-2">
          <Button type="submit" loading={save.isPending}>Save source</Button>
          <Button type="button" variant="ghost" onClick={() => setEditing(null)}>Cancel</Button>
        </div>
      </FormSection>
    </form>
  );

  return (
    <>
      <AdminTitle
        title="Source registry"
        description="Every source cited across projects, legislation, elections and news. Content links to these records, so a URL is never duplicated."
        actions={<Button onClick={() => { setF(EMPTY); setEditing("new"); }}><Plus /> Add source</Button>}
      />
      {editor}
      <div className="mb-5"><SearchBox value={q} onChange={setQ} placeholder="Search sources" /></div>
      <DataTable
        rows={data?.data}
        loading={isLoading}
        error={error}
        onRetry={() => refetch()}
        page={page}
        totalPages={data?.meta.total_pages}
        onPage={setPage}
        empty="No sources yet"
        columns={[
          {
            header: "Source",
            cell: (s) => (
              <button type="button" className="text-left" onClick={() => { setF(toForm(s)); setEditing(s.id); window.scrollTo({ top: 0, behavior: "smooth" }); }}>
                <span className="block font-semibold text-navy hover:text-green-600">{s.name}</span>
                {s.title && <span className="block text-xs text-muted-foreground">{s.title}</span>}
              </button>
            ),
          },
          { header: "Type", cell: (s) => SOURCE_TYPES[s.source_type] ?? s.source_type },
          { header: "Reliability", cell: (s) => RELIABILITY[s.reliability_level] ?? s.reliability_level },
          { header: "Cited by", cell: (s) => s.usage_count ?? 0 },
          {
            header: "Link",
            cell: (s) =>
              s.url ? (
                <a href={s.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-green-700 hover:underline" aria-label={`Open ${s.name}`}>
                  Open <ExternalLink className="size-3.5" />
                </a>
              ) : (
                "—"
              ),
          },
          {
            header: "",
            cell: (s) =>
              !s.usage_count && (
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-red-600"
                  aria-label={`Delete ${s.name}`}
                  onClick={async () => {
                    if (await confirm({ title: "Delete this source?", description: "It is not cited by any content.", confirmLabel: "Delete", destructive: true })) {
                      await api.del(`/api/admin/sources/${s.id}`);
                      toast.success("Source deleted");
                      qc.invalidateQueries({ queryKey: ["admin"] });
                    }
                  }}
                >
                  <Trash2 />
                </Button>
              ),
          },
        ]}
      />
    </>
  );
}
