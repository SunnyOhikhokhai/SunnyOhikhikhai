import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Field } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { api, getData } from "@/lib/api";
import type { Council } from "@/lib/types";
import { cn } from "@/lib/utils";
import { FormSection, MarkdownEditor, UploadButton } from "./editor-kit";
import { AdminTitle } from "./shared";

export default function Councils() {
  const { user } = useAuth();
  const scoped = user?.admin?.role === "area_council_admin" ? user.admin.area_council?.slug : undefined;
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["councils"], queryFn: () => getData<Council[]>("/api/area-councils") });
  const list = data?.filter((c) => !scoped || c.slug === scoped);
  const [slug, setSlug] = useState<string>();
  const current = list?.find((c) => c.slug === (slug ?? list[0]?.slug));
  const [f, setF] = useState({ summary: "", description: "", headquarters: "", image_url: "", wards: "" });
  useEffect(() => {
    if (current) setF({ summary: current.summary, description: current.description, headquarters: current.headquarters ?? "", image_url: current.image_url ?? "", wards: current.wards.join("\n") });
  }, [current]);
  const save = useMutation({
    mutationFn: () => api.put(`/api/admin/area-councils/${current!.slug}`, { ...f, image_url: f.image_url || null, headquarters: f.headquarters || null, wards: f.wards.split("\n").map((w) => w.trim()).filter(Boolean) }),
    onSuccess: () => { toast.success("Area Council updated"); qc.invalidateQueries({ queryKey: ["councils"] }); qc.invalidateQueries({ queryKey: ["council"] }); },
    onError: (e: Error) => toast.error(e.message),
  });
  if (!list) return <Skeleton className="h-96" />;
  return (
    <>
      <AdminTitle title="Area Councils" description="Manage council profile information. Publish local updates from News, Events and Announcements." />
      <div className="no-scrollbar mb-6 flex gap-2 overflow-x-auto">
        {list.map((c) => (
          <button key={c.slug} onClick={() => setSlug(c.slug)} className={cn("shrink-0 rounded-full px-4 py-2 text-sm font-semibold", current?.slug === c.slug ? "bg-navy text-white" : "bg-white text-slate-600 ring-1 ring-border")}>{c.short_name}</button>
        ))}
      </div>
      {current && (
        <form className="grid gap-6 xl:grid-cols-[1fr_340px]" onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
          <FormSection title={current.name} description="Only enter verified information. Leave facts out until they can be confirmed.">
            <Field id="c-sum" label="Summary" hint="Shown on council cards and the map."><Textarea value={f.summary} onChange={(e) => setF({ ...f, summary: e.target.value })} maxLength={600} className="min-h-[80px]" /></Field>
            <div className="space-y-1.5"><label htmlFor="c-desc" className="text-sm font-semibold text-navy-900">Overview</label><MarkdownEditor id="c-desc" value={f.description} onChange={(v) => setF({ ...f, description: v })} /></div>
            <Button type="submit" loading={save.isPending}>Save changes</Button>
          </FormSection>
          <aside className="space-y-6">
            <FormSection title="Details">
              <Field id="c-hq" label="Headquarters" optional><Input value={f.headquarters} onChange={(e) => setF({ ...f, headquarters: e.target.value })} /></Field>
              <Field id="c-wards" label="Wards" optional hint="One per line. Members can pick from these when registering."><Textarea value={f.wards} onChange={(e) => setF({ ...f, wards: e.target.value })} className="min-h-[140px]" /></Field>
            </FormSection>
            <FormSection title="Cover image">
              {f.image_url && <img src={f.image_url} alt="" className="aspect-video w-full rounded-xl object-cover" />}
              <UploadButton folder="councils" onUploaded={(url) => setF({ ...f, image_url: url })} label={f.image_url ? "Replace" : "Upload image"} />
            </FormSection>
          </aside>
        </form>
      )}
    </>
  );
}
