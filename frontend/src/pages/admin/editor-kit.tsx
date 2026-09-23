import { Eye, Loader2, Pencil, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { Markdown } from "@/components/shared/Markdown";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/input";
import { api } from "@/lib/api";
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
