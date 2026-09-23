import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MessageSquarePlus, MessagesSquare, Search, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { DiscussionRow } from "@/components/shared/cards";
import { PageHeader } from "@/components/shared/PageHeader";
import { Pagination } from "@/components/shared/Pagination";
import { Seo } from "@/components/shared/Seo";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input, Select, Textarea } from "@/components/ui/input";
import { Field } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { useDebounce } from "@/hooks/useDebounce";
import { useMeta } from "@/hooks/useMeta";
import { api, ApiError, type Paged } from "@/lib/api";
import type { DiscussionItem } from "@/lib/types";
import { cn } from "@/lib/utils";

function NewDiscussion({ open, onOpenChange, defaultCouncil }: { open: boolean; onOpenChange: (o: boolean) => void; defaultCouncil?: string }) {
  const meta = useMeta();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [form, setForm] = useState({ title: "", body: "", category: "general-discussion", area_council: defaultCouncil ?? "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  useEffect(() => setForm((f) => ({ ...f, area_council: defaultCouncil ?? f.area_council })), [defaultCouncil]);
  const m = useMutation({
    mutationFn: () => api.post<{ data: DiscussionItem }>("/api/discussions", { ...form, area_council: form.area_council || null }),
    onSuccess: (res) => {
      toast.success("Your discussion has been posted.");
      qc.invalidateQueries({ queryKey: ["discussions"] });
      onOpenChange(false);
      navigate(`/community/${res.data.id}`);
    },
    onError: (e: Error) => {
      if (e instanceof ApiError && e.fields) setErrors(e.fields);
      toast.error(e.message);
    },
  });
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Start a discussion</DialogTitle>
          <DialogDescription>
            Keep it constructive. Don't share phone numbers, addresses or other personal information.{" "}
            <Link to="/community-guidelines" className="font-semibold text-green-600" onClick={() => onOpenChange(false)}>Community guidelines</Link>
          </DialogDescription>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            setErrors({});
            m.mutate();
          }}
        >
          <Field id="d-title" label="Title" error={errors.title}>
            <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required minLength={8} maxLength={200} placeholder="What would you like to discuss?" />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field id="d-cat" label="Category">
              <Select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                {meta.data?.discussion_categories.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}
              </Select>
            </Field>
            <Field id="d-council" label="Area Council" optional>
              <Select value={form.area_council} onChange={(e) => setForm({ ...form, area_council: e.target.value })}>
                <option value="">FCT-wide</option>
                {meta.data?.area_councils.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}
              </Select>
            </Field>
          </div>
          <Field id="d-body" label="Your post" error={errors.body} hint="At least 20 characters. Basic formatting (**bold**, lists) is supported.">
            <Textarea value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} required minLength={20} maxLength={10000} className="min-h-[160px]" />
          </Field>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" loading={m.isPending}>Post discussion</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function Community() {
  const { user } = useAuth();
  const meta = useMeta();
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");
  const dq = useDebounce(q, 350);
  const [composeOpen, setComposeOpen] = useState(false);
  const category = params.get("category") ?? "";
  const page = Number(params.get("page") ?? 1);

  useEffect(() => {
    if (params.get("new") && user?.email_verified) setComposeOpen(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const query = { category, area_council: params.get("area_council") ?? "", sort: params.get("sort") ?? "active", q: dq, page };
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["discussions", query],
    queryFn: () => api.get<Paged<DiscussionItem>>("/api/discussions", query),
    placeholderData: keepPreviousData,
  });
  const set = (k: string, v: string) => {
    const n = new URLSearchParams(params);
    if (v) n.set(k, v);
    else n.delete(k);
    n.delete("page");
    n.delete("new");
    setParams(n);
  };

  const startButton = !user ? (
    <Button asChild><Link to="/login?next=/community?new=1"><MessageSquarePlus /> Log in to post</Link></Button>
  ) : !user.email_verified ? (
    <Button asChild variant="white"><Link to="/settings?tab=verification">Verify email to post</Link></Button>
  ) : (
    <Button onClick={() => setComposeOpen(true)}><MessageSquarePlus /> Start a discussion</Button>
  );

  return (
    <>
      <Seo title="Community" description="Moderated community discussions for residents and members across the FCT." />
      <PageHeader eyebrow="Community" title="Community discussions" description="Share ideas, ask questions and connect with residents across the six Area Councils. All discussions are moderated." crumbs={[{ to: "/", label: "Home" }, { label: "Community" }]} actions={startButton} />
      <div className="container grid gap-10 py-8 lg:grid-cols-[1fr_300px]">
        <div className="min-w-0">
          <div className="no-scrollbar -mx-4 mb-4 flex gap-2 overflow-x-auto px-4 lg:mx-0 lg:px-0">
            {[{ slug: "", name: "All" }, ...(meta.data?.discussion_categories ?? [])].map((c) => (
              <button key={c.slug} onClick={() => set("category", c.slug)} aria-pressed={category === c.slug} className={cn("shrink-0 rounded-full px-4 py-2 text-sm font-semibold transition", category === c.slug ? "bg-navy text-white" : "bg-surface text-slate-600 ring-1 ring-border hover:text-navy")}>
                {c.name}
              </button>
            ))}
          </div>
          <div className="mb-6 grid gap-2 sm:grid-cols-[1fr_180px_150px]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
              <Input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search discussions" className="pl-10" aria-label="Search discussions" />
            </div>
            <Select aria-label="Area Council" value={params.get("area_council") ?? ""} onChange={(e) => set("area_council", e.target.value)}>
              <option value="">All councils</option>
              {meta.data?.area_councils.map((c) => <option key={c.slug} value={c.slug}>{c.short_name}</option>)}
            </Select>
            <Select aria-label="Sort" value={params.get("sort") ?? "active"} onChange={(e) => set("sort", e.target.value)}>
              <option value="active">Most recent activity</option>
              <option value="new">Newest</option>
              <option value="popular">Most popular</option>
            </Select>
          </div>
          {error ? (
            <ErrorState error={error} onRetry={() => refetch()} />
          ) : isLoading ? (
            <div className="space-y-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>
          ) : !data?.data.length ? (
            <EmptyState icon={MessagesSquare} title="No discussions here yet" description="Be the first to start a constructive conversation." action={startButton} />
          ) : (
            <div className="space-y-4">{data.data.map((d) => <DiscussionRow key={d.id} d={d} />)}</div>
          )}
          {data && <Pagination page={page} totalPages={data.meta.total_pages} onChange={(p) => { const n = new URLSearchParams(params); n.set("page", String(p)); setParams(n); }} />}
        </div>
        <aside className="space-y-5">
          <div className="rounded-2xl bg-navy p-6 text-white">
            <ShieldCheck className="size-7 text-green-400" />
            <h2 className="mt-3 text-lg font-bold text-white">Community guidelines</h2>
            <ul className="mt-3 space-y-2 text-sm text-navy-100">
              <li>• Be respectful and constructive</li>
              <li>• No hate speech, threats or harassment</li>
              <li>• No impersonation or doxxing</li>
              <li>• Don't share personal information</li>
              <li>• Don't present unverified claims as fact</li>
            </ul>
            <Link to="/community-guidelines" className="mt-4 inline-block text-sm font-semibold text-green-300 hover:text-white">Read the full guidelines →</Link>
          </div>
          <div className="rounded-2xl border border-border p-5 text-sm text-muted-foreground">
            Posts are members' own views and are <strong className="text-navy">user-generated content</strong>, not verified information from NIPAM. Use <strong className="text-navy">Report</strong> on anything that breaks the guidelines.
          </div>
        </aside>
      </div>
      {user?.email_verified && <NewDiscussion open={composeOpen} onOpenChange={setComposeOpen} defaultCouncil={params.get("area_council") ?? user.area_council?.slug} />}
    </>
  );
}
