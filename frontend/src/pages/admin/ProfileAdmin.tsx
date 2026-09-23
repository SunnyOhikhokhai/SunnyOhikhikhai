import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Portrait } from "@/components/brand/Portrait";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Field } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { PrincipalProfile } from "@/lib/types";
import { useProfile } from "../Aduda";
import { FormSection, MarkdownEditor, UploadButton } from "./editor-kit";
import { AdminTitle } from "./shared";

type Form = Omit<PrincipalProfile, "updated_at">;

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
    mutationFn: () => api.put("/api/admin/profile", { ...f, photo_url: f?.photo_url || null, photo_alt: f?.photo_alt || null }),
    onSuccess: () => {
      toast.success("Profile published");
      qc.invalidateQueries({ queryKey: ["profile"] });
      qc.invalidateQueries({ queryKey: ["home"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });
  if (!f) return <Skeleton className="h-96" />;
  const set = <K extends keyof Form>(k: K, v: Form[K]) => setF((x) => (x ? { ...x, [k]: v } : x));
  const setItem = <K extends "timeline" | "gallery" | "links">(k: K, i: number, patch: Partial<Form[K][number]>) =>
    setF((x) => (x ? { ...x, [k]: (x[k] as object[]).map((it, j) => (j === i ? { ...it, ...patch } : it)) } : x));
  const remove = (k: "timeline" | "gallery" | "links", i: number) => setF((x) => (x ? { ...x, [k]: (x[k] as object[]).filter((_, j) => j !== i) } : x));

  return (
    <form onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
      <AdminTitle
        title="Sen. Philip Aduda profile"
        description="Shown on the homepage and the Sen. Aduda page. Only publish verified information; give each milestone a source."
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
            <Field id="p-tag" label="Tagline" optional hint="A short, official slogan or motto."><Input value={f.tagline} onChange={(e) => set("tagline", e.target.value)} maxLength={300} /></Field>
            <Field id="p-sum" label="Summary" hint="Two or three sentences shown on the homepage."><Textarea value={f.summary} onChange={(e) => set("summary", e.target.value)} maxLength={2000} /></Field>
            <div className="space-y-1.5"><label htmlFor="p-bio" className="text-sm font-semibold text-navy-900">Full biography</label><MarkdownEditor id="p-bio" value={f.biography} onChange={(v) => set("biography", v)} rows={16} /></div>
          </FormSection>

          <FormSection title="Timeline of public service" description="Each milestone should cite where the information comes from.">
            {f.timeline.map((t, i) => (
              <div key={i} className="grid gap-3 rounded-xl bg-surface p-4 sm:grid-cols-[120px_1fr]">
                <Field id={`t-y-${i}`} label="Year"><Input value={t.year} onChange={(e) => setItem("timeline", i, { year: e.target.value })} /></Field>
                <Field id={`t-t-${i}`} label="Milestone"><Input value={t.title} onChange={(e) => setItem("timeline", i, { title: e.target.value })} required /></Field>
                <Field id={`t-d-${i}`} label="Description" optional className="sm:col-span-2"><Textarea value={t.description} onChange={(e) => setItem("timeline", i, { description: e.target.value })} className="min-h-[70px]" /></Field>
                <Field id={`t-s-${i}`} label="Source" className="sm:col-span-2"><Input value={t.source} onChange={(e) => setItem("timeline", i, { source: e.target.value })} placeholder="e.g. National Assembly records, 2011" /></Field>
                <div><Button type="button" size="sm" variant="ghost" className="text-red-600" onClick={() => remove("timeline", i)}><Trash2 /> Remove</Button></div>
              </div>
            ))}
            <Button type="button" size="sm" variant="outline" onClick={() => set("timeline", [...f.timeline, { year: "", title: "", description: "", source: "" }])}><Plus /> Add milestone</Button>
          </FormSection>

          <FormSection title="Gallery">
            <div className="grid gap-4 sm:grid-cols-2">
              {f.gallery.map((g, i) => (
                <div key={i} className="space-y-2 rounded-xl bg-surface p-3">
                  <img src={g.url} alt="" className="aspect-[4/3] w-full rounded-lg object-cover" />
                  <Input aria-label="Alt text" placeholder="Alt text (describe the photo)" value={g.alt} onChange={(e) => setItem("gallery", i, { alt: e.target.value })} required />
                  <Input aria-label="Caption" placeholder="Caption (optional)" value={g.caption} onChange={(e) => setItem("gallery", i, { caption: e.target.value })} />
                  <Button type="button" size="sm" variant="ghost" className="text-red-600" onClick={() => remove("gallery", i)}><Trash2 /> Remove</Button>
                </div>
              ))}
            </div>
            <UploadButton folder="content" label="Upload photo" onUploaded={(url) => set("gallery", [...f.gallery, { url, alt: "", caption: "" }])} />
          </FormSection>
        </div>

        <aside className="space-y-6">
          <FormSection title="Official photo">
            <div className="overflow-hidden rounded-2xl"><Portrait src={f.photo_url} alt={f.photo_alt} className="aspect-[4/5] w-full" /></div>
            <UploadButton folder="content" label={f.photo_url ? "Replace photo" : "Upload photo"} onUploaded={(url) => set("photo_url", url)} />
            {f.photo_url && <Field id="p-alt" label="Photo description (alt text)"><Input value={f.photo_alt ?? ""} onChange={(e) => set("photo_alt", e.target.value)} required /></Field>}
          </FormSection>
          <FormSection title="Official channels" description="Social media pages and websites.">
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
