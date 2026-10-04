import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Portrait } from "@/components/brand/Portrait";
import { Button } from "@/components/ui/button";
import { Input, Select, Textarea } from "@/components/ui/input";
import { Field } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { VERIFICATION } from "@/lib/constants";
import type { PrincipalProfile, VerificationStatus } from "@/lib/types";
import { useProfile } from "../Aduda";
import { FormSection, MarkdownEditor, UploadButton } from "./editor-kit";
import { AdminTitle } from "./shared";

type Form = Omit<PrincipalProfile, "updated_at">;
type ListKey = "timeline" | "gallery" | "links" | "badges" | "facts" | "metrics";

/** Verification + source inputs shared by badges, facts and milestones. */
function SourcedInputs({
  idp,
  item,
  onChange,
}: {
  idp: string;
  item: { verification?: VerificationStatus; source_name?: string; source_url?: string };
  onChange: (patch: { verification?: VerificationStatus; source_name?: string; source_url?: string }) => void;
}) {
  return (
    <div className="grid gap-3 sm:col-span-2 sm:grid-cols-3">
      <Field id={`${idp}-v`} label="Verification">
        <Select value={item.verification ?? "pending"} onChange={(e) => onChange({ verification: e.target.value as VerificationStatus })}>
          {Object.entries(VERIFICATION).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </Select>
      </Field>
      <Field id={`${idp}-sn`} label="Source name"><Input value={item.source_name ?? ""} onChange={(e) => onChange({ source_name: e.target.value })} placeholder="e.g. INEC" /></Field>
      <Field id={`${idp}-su`} label="Source URL" optional><Input type="url" value={item.source_url ?? ""} onChange={(e) => onChange({ source_url: e.target.value })} placeholder="https://" /></Field>
    </div>
  );
}

export default function ProfileAdmin() {
  const { data } = useProfile();
  const qc = useQueryClient();
  const [f, setF] = useState<Form | null>(null);
  useEffect(() => {
    if (data) {
      const { updated_at: _ignored, ...rest } = data;
      setF(rest);
    }
  }, [data]);
  const save = useMutation({
    mutationFn: () => {
      const nullable = ["photo_url", "photo_alt", "photo_caption", "photo_source_name", "photo_source_url", "photo_usage", "photo_rights_status", "metrics_note", "metrics_source_url"] as const;
      const body: Record<string, unknown> = { ...f };
      for (const k of nullable) body[k] = f?.[k] || null;
      body.timeline = f?.timeline.map((t) => ({ ...t, source_name: t.source_name ?? "", verification: t.verification ?? "pending" }));
      return api.put("/api/admin/profile", body);
    },
    onSuccess: () => {
      toast.success("Profile published");
      qc.invalidateQueries({ queryKey: ["profile"] });
      qc.invalidateQueries({ queryKey: ["home"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });
  if (!f) return <Skeleton className="h-96" />;
  const set = <K extends keyof Form>(k: K, v: Form[K]) => setF((x) => (x ? { ...x, [k]: v } : x));
  const setItem = <K extends ListKey>(k: K, i: number, patch: Partial<Form[K][number]>) =>
    setF((x) => (x ? { ...x, [k]: (x[k] as object[]).map((it, j) => (j === i ? { ...it, ...patch } : it)) } : x));
  const remove = (k: ListKey, i: number) => setF((x) => (x ? { ...x, [k]: (x[k] as object[]).filter((_, j) => j !== i) } : x));

  return (
    <form onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
      <AdminTitle
        title="Senator profile"
        description="Shown on the homepage and profile page. Give every fact and milestone a source and a verification status."
        actions={
          <>
            <Button asChild variant="ghost"><Link to="/philip-aduda" target="_blank"><ExternalLink /> View page</Link></Button>
            <Button type="submit" loading={save.isPending}>Save & publish</Button>
          </>
        }
      />
      <div className="grid gap-6 xl:grid-cols-[1fr_340px]">
        <div className="space-y-6">
          <FormSection title="Introduction">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field id="p-name" label="Name"><Input value={f.name} onChange={(e) => set("name", e.target.value)} required /></Field>
              <Field id="p-title" label="Title / position" optional><Input value={f.title} onChange={(e) => set("title", e.target.value)} /></Field>
            </div>
            <Field id="p-tag" label="Second status line" optional hint="e.g. APC Candidate — FCT Senatorial District, 2027"><Input value={f.tagline} onChange={(e) => set("tagline", e.target.value)} maxLength={300} /></Field>
            <Field id="p-sum" label="Summary" hint="Two or three sentences shown on the homepage."><Textarea value={f.summary} onChange={(e) => set("summary", e.target.value)} maxLength={2000} /></Field>
            <div className="space-y-1.5"><label htmlFor="p-bio" className="text-sm font-semibold text-navy-900">Full biography</label><MarkdownEditor id="p-bio" value={f.biography} onChange={(v) => set("biography", v)} rows={16} /></div>
          </FormSection>

          <FormSection title="Status badges" description="Shown under the name, e.g. “Former FCT Senator (2011–2023)”. Do not describe him as the sitting senator.">
            {f.badges.map((b, i) => (
              <div key={i} className="grid gap-3 rounded-xl bg-surface p-4 sm:grid-cols-2">
                <Field id={`b-l-${i}`} label="Badge text" className="sm:col-span-2"><Input value={b.label} onChange={(e) => setItem("badges", i, { label: e.target.value })} required minLength={2} /></Field>
                <SourcedInputs idp={`b-${i}`} item={b} onChange={(patch) => setItem("badges", i, patch)} />
                <div><Button type="button" size="sm" variant="ghost" className="text-red-600" onClick={() => remove("badges", i)}><Trash2 /> Remove</Button></div>
              </div>
            ))}
            <Button type="button" size="sm" variant="outline" onClick={() => set("badges", [...f.badges, { label: "", verification: "pending", source_name: "", source_url: "" }])}><Plus /> Add badge</Button>
          </FormSection>

          <FormSection title="At a glance — facts" description="Date of birth, education, honours and so on. Where sources disagree, add one fact per source.">
            {f.facts.map((x, i) => (
              <div key={i} className="grid gap-3 rounded-xl bg-surface p-4 sm:grid-cols-2">
                <Field id={`f-l-${i}`} label="Label"><Input value={x.label} onChange={(e) => setItem("facts", i, { label: e.target.value })} required minLength={2} /></Field>
                <Field id={`f-v-${i}`} label="Value"><Input value={x.value} onChange={(e) => setItem("facts", i, { value: e.target.value })} required /></Field>
                <Field id={`f-n-${i}`} label="Note" optional className="sm:col-span-2"><Input value={x.note ?? ""} onChange={(e) => setItem("facts", i, { note: e.target.value })} /></Field>
                <SourcedInputs idp={`f-${i}`} item={x} onChange={(patch) => setItem("facts", i, patch)} />
                <div><Button type="button" size="sm" variant="ghost" className="text-red-600" onClick={() => remove("facts", i)}><Trash2 /> Remove</Button></div>
              </div>
            ))}
            <Button type="button" size="sm" variant="outline" onClick={() => set("facts", [...f.facts, { label: "", value: "", note: "", verification: "pending", source_name: "", source_url: "" }])}><Plus /> Add fact</Button>
          </FormSection>

          <FormSection title="Self-reported figures" description="Figures from his official platform. They are always shown with the label below and a Self-reported badge — never as audited totals.">
            <div className="grid gap-3 sm:grid-cols-2">
              {f.metrics.map((m, i) => (
                <div key={i} className="flex items-end gap-2 rounded-xl bg-surface p-3">
                  <Field id={`m-v-${i}`} label="Figure" className="w-24"><Input value={m.value} onChange={(e) => setItem("metrics", i, { value: e.target.value })} required /></Field>
                  <Field id={`m-l-${i}`} label="Label" className="flex-1"><Input value={m.label} onChange={(e) => setItem("metrics", i, { label: e.target.value })} required minLength={2} /></Field>
                  <Button type="button" size="sm" variant="ghost" className="text-red-600" aria-label="Remove figure" onClick={() => remove("metrics", i)}><Trash2 /></Button>
                </div>
              ))}
            </div>
            <Button type="button" size="sm" variant="outline" onClick={() => set("metrics", [...f.metrics, { value: "", label: "" }])}><Plus /> Add figure</Button>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field id="m-note" label="Label shown with the figures"><Input value={f.metrics_note ?? ""} onChange={(e) => set("metrics_note", e.target.value)} maxLength={300} /></Field>
              <Field id="m-src" label="Source URL" optional><Input type="url" value={f.metrics_source_url ?? ""} onChange={(e) => set("metrics_source_url", e.target.value)} /></Field>
            </div>
          </FormSection>

          <FormSection title="Political timeline" description="Each milestone cites its source and verification status.">
            {f.timeline.map((t, i) => (
              <div key={i} className="grid gap-3 rounded-xl bg-surface p-4 sm:grid-cols-[120px_1fr]">
                <Field id={`t-y-${i}`} label="Year"><Input value={t.year} onChange={(e) => setItem("timeline", i, { year: e.target.value })} /></Field>
                <Field id={`t-t-${i}`} label="Milestone"><Input value={t.title} onChange={(e) => setItem("timeline", i, { title: e.target.value })} required /></Field>
                <Field id={`t-d-${i}`} label="Description" optional className="sm:col-span-2"><Textarea value={t.description} onChange={(e) => setItem("timeline", i, { description: e.target.value })} className="min-h-[70px]" /></Field>
                <SourcedInputs
                  idp={`t-${i}`}
                  item={{ verification: t.verification, source_name: t.source_name, source_url: t.source }}
                  onChange={(patch) => setItem("timeline", i, { verification: patch.verification ?? t.verification, source_name: patch.source_name ?? t.source_name, source: patch.source_url ?? t.source })}
                />
                <div><Button type="button" size="sm" variant="ghost" className="text-red-600" onClick={() => remove("timeline", i)}><Trash2 /> Remove</Button></div>
              </div>
            ))}
            <Button type="button" size="sm" variant="outline" onClick={() => set("timeline", [...f.timeline, { year: "", title: "", description: "", source: "", source_name: "", verification: "pending" }])}><Plus /> Add milestone</Button>
          </FormSection>

          <FormSection title="Gallery" description="Only official or permitted images. Record where each came from and its usage rights.">
            <div className="grid gap-4 sm:grid-cols-2">
              {f.gallery.map((g, i) => (
                <div key={i} className="space-y-2 rounded-xl bg-surface p-3">
                  <img src={g.url} alt="" className="aspect-[4/3] w-full rounded-lg object-cover" />
                  <Input aria-label="Alt text" placeholder="Alt text (describe the photo)" value={g.alt} onChange={(e) => setItem("gallery", i, { alt: e.target.value })} required />
                  <Input aria-label="Caption" placeholder="Caption (optional)" value={g.caption} onChange={(e) => setItem("gallery", i, { caption: e.target.value })} />
                  <Input aria-label="Source name" placeholder="Source name, e.g. official website" value={g.source_name ?? ""} onChange={(e) => setItem("gallery", i, { source_name: e.target.value })} />
                  <Input aria-label="Source URL" type="url" placeholder="Source URL (https://…)" value={g.source_url ?? ""} onChange={(e) => setItem("gallery", i, { source_url: e.target.value })} />
                  <Input aria-label="Date" placeholder="Date, if known" value={g.date ?? ""} onChange={(e) => setItem("gallery", i, { date: e.target.value })} />
                  <Input aria-label="Usage rights" placeholder="Usage rights, e.g. permission granted by media team" value={g.usage_rights_status ?? ""} onChange={(e) => setItem("gallery", i, { usage_rights_status: e.target.value })} />
                  <Button type="button" size="sm" variant="ghost" className="text-red-600" onClick={() => remove("gallery", i)}><Trash2 /> Remove</Button>
                </div>
              ))}
            </div>
            <UploadButton folder="content" label="Upload photo" onUploaded={(url) => set("gallery", [...f.gallery, { url, alt: "", caption: "" }])} />
          </FormSection>
        </div>

        <aside className="space-y-6">
          <FormSection title="Official portrait" description="Upload the portrait from his official website once it has been obtained with permission. It is not shown until uploaded.">
            <div className="overflow-hidden rounded-2xl"><Portrait src={f.photo_url} alt={f.photo_alt} className="aspect-[4/5] w-full" /></div>
            <UploadButton folder="content" label={f.photo_url ? "Replace photo" : "Upload photo"} onUploaded={(url) => set("photo_url", url)} />
            {f.photo_url && <Field id="p-alt" label="Photo description (alt text)"><Input value={f.photo_alt ?? ""} onChange={(e) => set("photo_alt", e.target.value)} required /></Field>}
            <Field id="p-cap" label="Caption" optional><Input value={f.photo_caption ?? ""} onChange={(e) => set("photo_caption", e.target.value)} maxLength={300} /></Field>
            <Field id="p-srcn" label="Source name"><Input value={f.photo_source_name ?? ""} onChange={(e) => set("photo_source_name", e.target.value)} maxLength={200} /></Field>
            <Field id="p-srcu" label="Source URL"><Input type="url" value={f.photo_source_url ?? ""} onChange={(e) => set("photo_source_url", e.target.value)} /></Field>
            <Field id="p-use" label="Usage" optional><Input value={f.photo_usage ?? ""} onChange={(e) => set("photo_usage", e.target.value)} maxLength={200} /></Field>
            <Field id="p-rights" label="Usage rights status" optional><Textarea value={f.photo_rights_status ?? ""} onChange={(e) => set("photo_rights_status", e.target.value)} maxLength={300} className="min-h-[70px]" /></Field>
          </FormSection>
          <FormSection title="Official links" description="Official website, party profile, INEC documents and social media pages.">
            {f.links.map((l, i) => (
              <div key={i} className="space-y-2 rounded-xl bg-surface p-3">
                <Input aria-label="Label" placeholder="e.g. Facebook" value={l.label} onChange={(e) => setItem("links", i, { label: e.target.value })} required />
                <Input aria-label="URL" type="url" placeholder="https://" value={l.url} onChange={(e) => setItem("links", i, { url: e.target.value })} required />
                <Button type="button" size="sm" variant="ghost" className="text-red-600" onClick={() => remove("links", i)}><Trash2 /> Remove</Button>
              </div>
            ))}
            <Button type="button" size="sm" variant="outline" onClick={() => set("links", [...f.links, { label: "", url: "" }])}><Plus /> Add link</Button>
          </FormSection>
        </aside>
      </div>
    </form>
  );
}
