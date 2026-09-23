import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { EyeOff, Lock, Pin, Plus, ShieldCheck, Trash2, Undo2, UserX } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useConfirm } from "@/components/ui/confirm";
import { Input, Select } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, type Paged } from "@/lib/api";
import { REPORT_REASONS } from "@/lib/constants";
import type { DiscussionItem } from "@/lib/types";
import { timeAgo } from "@/lib/utils";
import { AdminTitle, DataTable, SearchBox, StatusBadge, useAdminList, useSearchState } from "./shared";

interface ReportRow {
  id: number;
  target_type: "discussion" | "comment";
  target_id: number;
  reason: string;
  details: string | null;
  status: string;
  resolution_note: string | null;
  created_at: string;
  reporter: string | null;
  target: { id: number; title: string | null; body: string; status: string; deleted: boolean; author: { id: number; name: string; status: string }; discussion_id: number } | null;
}

const reasonLabel = (r: string) => REPORT_REASONS.find(([k]) => k === r)?.[1] ?? r;

function Reports() {
  const qc = useQueryClient();
  const confirm = useConfirm();
  const [status, setStatus] = useState("open");
  const [page, setPage] = useState(1);
  const { data, isLoading, error, refetch } = useAdminList<ReportRow>("reports", "/api/admin/reports", { status, page });
  const resolve = useMutation({
    mutationFn: ({ id, action }: { id: number; action: string }) => api.post(`/api/admin/reports/${id}/resolve`, { action }),
    onSuccess: () => { toast.success("Report resolved"); qc.invalidateQueries({ queryKey: ["admin"] }); },
    onError: (e: Error) => toast.error(e.message),
  });
  const act = async (id: number, action: string, title: string) => {
    if (action === "dismiss" || (await confirm({ title, confirmLabel: "Confirm", destructive: true }))) resolve.mutate({ id, action });
  };
  return (
    <>
      <div className="mb-5">
        <Select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="h-10 w-44" aria-label="Report status">
          <option value="open">Open</option><option value="resolved">Resolved</option><option value="dismissed">Dismissed</option><option value="all">All</option>
        </Select>
      </div>
      {error ? <ErrorState error={error} onRetry={() => refetch()} /> : isLoading ? <Skeleton className="h-60" /> : !data?.data.length ? (
        <EmptyState icon={ShieldCheck} title={status === "open" ? "No open reports" : "Nothing here"} description="Reports from members will appear here for review." />
      ) : (
        <ul className="space-y-4">
          {data.data.map((r) => (
            <li key={r.id} className="rounded-2xl border border-border bg-white p-5 shadow-card">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="danger">{reasonLabel(r.reason)}</Badge>
                <Badge variant="outline" className="capitalize">{r.target_type}</Badge>
                <StatusBadge status={r.status} />
                <span className="ml-auto text-xs text-slate-500">{r.reporter ? `Reported ${timeAgo(r.created_at)} by ${r.reporter}` : `Held by the language filter ${timeAgo(r.created_at)}`}</span>
              </div>
              {r.details && <p className="mt-2 text-sm italic text-slate-600">“{r.details}”</p>}
              {r.target ? (
                <div className="mt-3 rounded-xl bg-surface p-4">
                  {r.target.title && <p className="font-semibold text-navy">{r.target.title}</p>}
                  <p className="mt-1 whitespace-pre-line text-sm text-slate-700">{r.target.body}</p>
                  <p className="mt-2 text-xs text-slate-500">
                    By <strong>{r.target.author.name}</strong> ({r.target.author.status}) · content status: {r.target.status}{r.target.deleted && " · deleted by author"} ·{" "}
                    <Link to={`/community/${r.target.discussion_id}`} target="_blank" className="font-semibold text-green-600">Open thread</Link>
                  </p>
                </div>
              ) : <p className="mt-3 text-sm text-muted-foreground">Content no longer exists.</p>}
              {r.status === "open" ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button size="sm" variant="outline" onClick={() => act(r.id, "dismiss", "")}><Undo2 /> {r.reporter ? "Dismiss" : "Approve & publish"}</Button>
                  <Button size="sm" variant="outline" onClick={() => act(r.id, "hide_content", "Hide this content?")}><EyeOff /> Hide</Button>
                  <Button size="sm" variant="destructive" onClick={() => act(r.id, "remove_content", "Remove this content?")}><Trash2 /> Remove content</Button>
                  <Button size="sm" variant="destructive" onClick={() => act(r.id, "suspend_author", "Remove content and suspend the author?")}><UserX /> Remove & suspend author</Button>
                </div>
              ) : r.resolution_note && <p className="mt-3 text-xs text-slate-500">Note: {r.resolution_note}</p>}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

function Discussions() {
  const qc = useQueryClient();
  const { q, setQ, dq } = useSearchState();
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading, error, refetch } = useAdminList<DiscussionItem>("discussions", "/api/admin/discussions", { q: dq, status, page });
  const patch = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Record<string, unknown> }) => api.patch(`/api/admin/discussions/${id}`, body),
    onSuccess: () => { toast.success("Discussion updated"); qc.invalidateQueries({ queryKey: ["admin", "discussions"] }); },
  });
  return (
    <>
      <div className="mb-5 flex flex-wrap gap-2">
        <SearchBox value={q} onChange={setQ} placeholder="Search discussions" />
        <Select value={status} onChange={(e) => setStatus(e.target.value)} className="h-10 w-40" aria-label="Status"><option value="">All</option><option value="visible">Visible</option><option value="hidden">Hidden</option><option value="removed">Removed</option></Select>
      </div>
      <DataTable
        rows={data?.data}
        loading={isLoading}
        error={error}
        onRetry={() => refetch()}
        page={page}
        totalPages={data?.meta.total_pages}
        onPage={setPage}
        columns={[
          { header: "Discussion", cell: (d) => <Link to={`/community/${d.id}`} target="_blank" className="font-semibold text-navy hover:text-green-600">{d.title}</Link> },
          { header: "Author", cell: (d) => d.author.name },
          { header: "Activity", cell: (d) => `${d.comment_count} comments · ${d.reaction_count} likes` },
          { header: "Status", cell: (d) => <span className="flex gap-1"><StatusBadge status={d.status} />{d.is_pinned && <Badge variant="navy">Pinned</Badge>}{d.is_locked && <Badge variant="outline">Locked</Badge>}</span> },
          {
            header: "",
            className: "text-right whitespace-nowrap",
            cell: (d) => (
              <span className="inline-flex gap-1">
                <Button size="sm" variant="ghost" aria-label={d.is_pinned ? "Unpin" : "Pin"} onClick={() => patch.mutate({ id: d.id, body: { is_pinned: !d.is_pinned } })}><Pin /></Button>
                <Button size="sm" variant="ghost" aria-label={d.is_locked ? "Unlock" : "Lock"} onClick={() => patch.mutate({ id: d.id, body: { is_locked: !d.is_locked } })}><Lock /></Button>
                {d.status === "visible" ? (
                  <Button size="sm" variant="ghost" className="text-red-600" onClick={() => patch.mutate({ id: d.id, body: { status: "removed" } })}><Trash2 /> Remove</Button>
                ) : (
                  <Button size="sm" variant="ghost" onClick={() => patch.mutate({ id: d.id, body: { status: "visible" } })}><Undo2 /> Restore</Button>
                )}
              </span>
            ),
          },
        ]}
      />
    </>
  );
}

interface Term { id: number; term: string; severity: "block" | "review"; category: string; is_active: boolean }

const CATEGORY_LABEL: Record<string, string> = { insult: "Insult", profanity: "Profanity", hate: "Hate / tribalism", threat: "Threat", other: "Other" };

function LanguageFilter() {
  const qc = useQueryClient();
  const confirm = useConfirm();
  const [f, setF] = useState({ term: "", severity: "block", category: "insult" });
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["admin", "blocked-terms"],
    queryFn: () => api.get<Paged<Term> & { meta: { blocked_last_24h: number } }>("/api/admin/blocked-terms"),
  });
  const refresh = () => qc.invalidateQueries({ queryKey: ["admin", "blocked-terms"] });
  const add = useMutation({
    mutationFn: () => api.post("/api/admin/blocked-terms", f),
    onSuccess: () => { toast.success(`"${f.term}" added to the filter`); setF({ ...f, term: "" }); refresh(); },
    onError: (e: Error) => toast.error(e.message),
  });
  const groups = (data?.data ?? []).reduce<Record<string, Term[]>>((acc, t) => ((acc[t.category] ??= []).push(t), acc), {});
  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
      <div className="space-y-5">
        <p className="rounded-2xl bg-surface p-4 text-sm text-slate-600 ring-1 ring-border">
          Words and phrases below are checked in every post, comment and public profile name — including disguised spellings like
          <code className="mx-1 rounded bg-white px-1">f.u.c.k</code>, <code className="mx-1 rounded bg-white px-1">st*pid</code> or
          <code className="mx-1 rounded bg-white px-1">1d10t</code>. <strong className="text-navy">Block</strong> rejects the post;{" "}
          <strong className="text-navy">Review</strong> hides it until a moderator approves it in the Reports queue. Members who hit the
          filter 5 times in 24 hours have posting paused for a day.
          {data && <span className="mt-2 block font-semibold text-navy">{data.meta.blocked_last_24h} abusive post attempt{data.meta.blocked_last_24h === 1 ? "" : "s"} blocked in the last 24 hours.</span>}
        </p>
        {error ? <ErrorState error={error} onRetry={() => refetch()} /> : isLoading ? <Skeleton className="h-60" /> : (
          Object.entries(groups).map(([cat, terms]) => (
            <section key={cat} className="rounded-2xl border border-border bg-white p-5 shadow-card">
              <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">{CATEGORY_LABEL[cat] ?? cat} ({terms.length})</h3>
              <ul className="flex flex-wrap gap-2">
                {terms.map((t) => (
                  <li key={t.id} className="flex items-center gap-1.5 rounded-full bg-surface py-1 pl-3 pr-1 text-sm ring-1 ring-border">
                    <span className="font-medium text-navy">{t.term}</span>
                    <Badge variant={t.severity === "block" ? "danger" : "demo"}>{t.severity}</Badge>
                    <button
                      aria-label={`Remove ${t.term}`}
                      className="rounded-full p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
                      onClick={async () => {
                        if (await confirm({ title: `Remove "${t.term}" from the filter?`, confirmLabel: "Remove", destructive: true })) {
                          await api.del(`/api/admin/blocked-terms/${t.id}`);
                          refresh();
                        }
                      }}
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ))
        )}
      </div>
      <form className="h-fit space-y-4 rounded-2xl border border-border bg-white p-5 shadow-card" onSubmit={(e) => { e.preventDefault(); add.mutate(); }}>
        <h3 className="text-base font-bold">Add a word or phrase</h3>
        <p className="text-sm text-muted-foreground">Add local-language insults, tribal slurs or phrases you see being misused.</p>
        <Input aria-label="Word or phrase" placeholder="Word or phrase" value={f.term} onChange={(e) => setF({ ...f, term: e.target.value })} required minLength={2} />
        <Select aria-label="Category" value={f.category} onChange={(e) => setF({ ...f, category: e.target.value })}>
          {Object.entries(CATEGORY_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </Select>
        <Select aria-label="Action" value={f.severity} onChange={(e) => setF({ ...f, severity: e.target.value })}>
          <option value="block">Block the post</option>
          <option value="review">Hold for moderator review</option>
        </Select>
        <Button type="submit" loading={add.isPending} className="w-full"><Plus /> Add to filter</Button>
      </form>
    </div>
  );
}

export default function Moderation() {
  return (
    <>
      <AdminTitle title="Moderation" description="Review reports and manage community discussions against the Community Guidelines. All actions are audit-logged." />
      <Tabs defaultValue="reports">
        <TabsList><TabsTrigger value="reports">Reports queue</TabsTrigger><TabsTrigger value="discussions">Discussions</TabsTrigger><TabsTrigger value="filter">Language filter</TabsTrigger></TabsList>
        <TabsContent value="reports"><Reports /></TabsContent>
        <TabsContent value="filter"><LanguageFilter /></TabsContent>
        <TabsContent value="discussions"><Discussions /></TabsContent>
      </Tabs>
    </>
  );
}
