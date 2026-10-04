import { useQuery } from "@tanstack/react-query";
import { Eye, Loader2, Pencil, Plus, Trash2, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { Markdown } from "@/components/shared/Markdown";
import { Button } from "@/components/ui/button";
import { Input, Select, Textarea } from "@/components/ui/input";
import { Field } from "@/components/ui/label";
import { api, getData } from "@/lib/api";
import { VERIFICATION } from "@/lib/constants";
import type { RegistrySource, VerificationStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

export function UploadButton({ folder, accept = "image/jpeg,image/png,image/webp", onUploaded, label = "Upload" }: { folder: string; accept?: string; onUploaded: (url: string) => void; label?: string }) {
  const ref = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  return (
    <>
      <input
        ref={ref}
        type="file"
        accept={accept}
        className="hidden"
        onChange={async (e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          setBusy(true);
          try {
            const fd = new FormData();
            fd.append("file", file);
            const res = await api.post<{ data: { url: string } }>(`/api/admin/uploads?folder=${folder}`, fd);
            onUploaded(res.data.url);
            toast.success("File uploaded");
          } catch (err) {
            toast.error((err as Error).message);
          } finally {
            setBusy(false);
            e.target.value = "";
          }
        }}
      />
      <Button type="button" variant="outline" size="sm" onClick={() => ref.current?.click()} disabled={busy}>
        {busy ? <Loader2 className="animate-spin" /> : <Upload />} {label}
      </Button>
    </>
  );
}

export function MarkdownEditor({ id, value, onChange, rows = 12 }: { id: string; value: string; onChange: (v: string) => void; rows?: number }) {
  const [preview, setPreview] = useState(false);
  return (
    <div className="overflow-hidden rounded-xl border border-border">
      <div className="flex items-center justify-between border-b border-border bg-surface px-3 py-1.5">
        <span className="text-xs text-muted-foreground">Markdown: **bold**, ## heading, - list, [link](https://…)</span>
        <button type="button" onClick={() => setPreview((p) => !p)} className="flex items-center gap-1 text-xs font-semibold text-navy hover:text-green-600">
          {preview ? <><Pencil className="size-3" /> Edit</> : <><Eye className="size-3" /> Preview</>}
        </button>
      </div>
      {preview ? (
        <div className="min-h-[12rem] p-4"><Markdown>{value || "_Nothing to preview_"}</Markdown></div>
      ) : (
        <Textarea id={id} value={value} onChange={(e) => onChange(e.target.value)} rows={rows} className={cn("rounded-none border-0 font-mono text-sm shadow-none focus-visible:ring-0")} />
      )}
    </div>
  );
}

export function FormSection({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-border bg-white p-5 shadow-card sm:p-6">
      <h2 className="text-base font-bold">{title}</h2>
      {description && <p className="mt-0.5 text-sm text-muted-foreground">{description}</p>}
      <div className="mt-5 space-y-4">{children}</div>
    </section>
  );
}

export type LinkedSrc = { name: string; url: string; title: string; note: string };

export const toLinked = (s: { name: string; url: string | null; title: string | null; note?: string | null }): LinkedSrc => ({
  name: s.name,
  url: s.url ?? "",
  title: s.title ?? "",
  note: s.note ?? "",
});

export const linkedPayload = (rows: LinkedSrc[]) =>
  rows.map((s) => ({ name: s.name, url: s.url || null, title: s.title || null, note: s.note || null }));

/** Cite sources from the registry (or add a new one, which joins the registry on save). */
export function LinkedSourcesEditor({ value, onChange }: { value: LinkedSrc[]; onChange: (v: LinkedSrc[]) => void }) {
  const registry = useQuery({
    queryKey: ["admin", "sources", "all"],
    queryFn: () => getData<RegistrySource[]>("/api/admin/sources", { page_size: 200 }),
  });
  const update = (i: number, patch: Partial<LinkedSrc>) => onChange(value.map((s, j) => (j === i ? { ...s, ...patch } : s)));
  return (
    <div className="space-y-3">
      {value.map((s, i) => (
        <div key={i} className="grid gap-3 rounded-xl bg-surface p-4 sm:grid-cols-2">
          <Field id={`ls-n-${i}`} label="Source name" hint="Publisher, e.g. INEC, Vanguard"><Input value={s.name} onChange={(e) => update(i, { name: e.target.value })} required minLength={2} /></Field>
          <Field id={`ls-u-${i}`} label="URL" optional><Input type="url" value={s.url} onChange={(e) => update(i, { url: e.target.value })} placeholder="https://" /></Field>
          <Field id={`ls-t-${i}`} label="Document / article title" optional><Input value={s.title} onChange={(e) => update(i, { title: e.target.value })} /></Field>
          <Field id={`ls-note-${i}`} label="What it supports" optional hint="e.g. Confirms the candidacy"><Input value={s.note} onChange={(e) => update(i, { note: e.target.value })} maxLength={300} /></Field>
          <div className="sm:col-span-2">
            <Button type="button" size="sm" variant="ghost" className="text-red-600" onClick={() => onChange(value.filter((_, j) => j !== i))}><Trash2 /> Remove source</Button>
          </div>
        </div>
      ))}
      <div className="flex flex-wrap gap-2">
        <Select
          aria-label="Add a source from the registry"
          className="h-9 w-auto max-w-full text-sm"
          value=""
          onChange={(e) => {
            const src = registry.data?.find((r) => String(r.id) === e.target.value);
            if (src) onChange([...value, toLinked(src)]);
          }}
        >
          <option value="">+ Cite a source from the registry…</option>
          {registry.data?.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}{r.title ? ` — ${r.title}` : ""}
            </option>
          ))}
        </Select>
        <Button type="button" variant="outline" size="sm" onClick={() => onChange([...value, { name: "", url: "", title: "", note: "" }])}><Plus /> New source</Button>
      </div>
    </div>
  );
}

export function VerificationSelect({ id, value, onChange, disabled }: { id: string; value: VerificationStatus; onChange: (v: VerificationStatus) => void; disabled?: boolean }) {
  return (
    <div className="space-y-1.5">
      <Field id={id} label="Verification">
        <Select value={value} disabled={disabled} onChange={(e) => onChange(e.target.value as VerificationStatus)}>
          {Object.entries(VERIFICATION).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </Select>
      </Field>
      <p className="text-xs text-muted-foreground">{(VERIFICATION[value] ?? VERIFICATION.pending).description}</p>
    </div>
  );
}
