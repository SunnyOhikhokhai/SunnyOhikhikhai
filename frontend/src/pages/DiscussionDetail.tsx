import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Heart, Lock, MessageSquare, Pin, Reply, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { Markdown } from "@/components/shared/Markdown";
import { ReportButton } from "@/components/shared/ReportDialog";
import { Seo } from "@/components/shared/Seo";
import { ErrorState } from "@/components/shared/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useConfirm } from "@/components/ui/confirm";
import { Textarea } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError, getData } from "@/lib/api";
import type { CommentItem, DiscussionItem } from "@/lib/types";
import { cn, initials, timeAgo } from "@/lib/utils";
import NotFound from "./NotFound";

type Thread = DiscussionItem & { comments: CommentItem[]; can_edit: boolean };

function Avatar({ name, team }: { name: string; team?: boolean }) {
  return (
    <span className={cn("flex size-9 shrink-0 items-center justify-center rounded-full text-xs font-bold", team ? "bg-green-600 text-white" : "bg-navy-100 text-navy")} aria-hidden>
      {initials(name)}
    </span>
  );
}

function LikeButton({ type, id, liked, count, onChange }: { type: "discussion" | "comment"; id: number; liked: boolean | null; count: number; onChange: () => void }) {
  const { user } = useAuth();
  const m = useMutation({
    mutationFn: () => api.post(`/api/reactions?target_type=${type}&target_id=${id}`),
    onSuccess: onChange,
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <button
      disabled={!user?.email_verified || m.isPending}
      onClick={() => m.mutate()}
      aria-pressed={!!liked}
      aria-label={liked ? "Unlike" : "Like"}
      title={!user ? "Log in to react" : !user.email_verified ? "Verify your email to react" : undefined}
      className={cn("inline-flex items-center gap-1.5 text-[13px] font-medium transition disabled:cursor-default", liked ? "text-green-600" : "text-slate-500 hover:text-green-600")}
    >
      <Heart className={cn("size-4", liked && "fill-current")} /> {count}
    </button>
  );
}

function CommentForm({ discussionId, parentId, onDone, autoFocus }: { discussionId: number; parentId?: number; onDone: () => void; autoFocus?: boolean }) {
  const [body, setBody] = useState("");
  const m = useMutation({
    mutationFn: () => api.post(`/api/discussions/${discussionId}/comments`, { body, parent_id: parentId ?? null }),
    onSuccess: () => {
      setBody("");
      onDone();
      toast.success(parentId ? "Reply posted" : "Comment posted");
    },
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (body.trim().length >= 2) m.mutate();
      }}
      className="space-y-2"
    >
      <label htmlFor={`c-${parentId ?? "root"}`} className="sr-only">{parentId ? "Write a reply" : "Write a comment"}</label>
      <Textarea id={`c-${parentId ?? "root"}`} autoFocus={autoFocus} value={body} onChange={(e) => setBody(e.target.value)} placeholder={parentId ? "Write a reply…" : "Add a constructive comment…"} maxLength={5000} className="min-h-[90px] bg-white" />
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-muted-foreground">Be respectful. No personal information.</p>
        <Button type="submit" size="sm" loading={m.isPending} disabled={body.trim().length < 2}>{parentId ? "Reply" : "Post comment"}</Button>
      </div>
    </form>
  );
}

export default function DiscussionDetail() {
  const { id = "" } = useParams();
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const confirm = useConfirm();
  const qc = useQueryClient();
  const [replyTo, setReplyTo] = useState<number | null>(null);
  const { data: d, isLoading, error, refetch } = useQuery({ queryKey: ["discussion", id], queryFn: () => getData<Thread>(`/api/discussions/${id}`) });
  const reload = () => qc.invalidateQueries({ queryKey: ["discussion", id] });

  const del = useMutation({
    mutationFn: (url: string) => api.del(url),
    onError: (e: Error) => toast.error(e.message),
  });

  if (error instanceof ApiError && error.status === 404) return <NotFound />;
  if (error) return <div className="container py-16"><ErrorState error={error} onRetry={() => refetch()} /></div>;
  if (isLoading || !d)
    return (
      <div className="container max-w-3xl space-y-4 py-12">
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-40" />
        <Skeleton className="h-24" />
      </div>
    );

  const roots = d.comments.filter((c) => !c.parent_id);
  const replies = (pid: number) => d.comments.filter((c) => c.parent_id === pid);
  const canComment = user?.email_verified && !d.is_locked;

  const renderComment = (c: CommentItem, nested = false) => (
    <li key={c.id} className={cn("flex gap-3", nested && "mt-4")}>
      <Avatar name={c.author.name} team={c.author.is_team} />
      <div className="min-w-0 flex-1">
        <div className={cn("rounded-2xl px-4 py-3", c.status === "visible" ? "bg-surface" : "bg-slate-50 italic text-slate-400")}>
          <p className="text-sm">
            <span className="font-semibold text-navy">{c.author.name}</span>
            {c.author.is_team && <span className="ml-1.5 text-xs font-semibold text-green-600">NIPAM Team</span>}
            <span className="ml-2 text-xs text-slate-500">{timeAgo(c.created_at)}</span>
          </p>
          <p className="mt-1 whitespace-pre-line break-words text-[15px] text-slate-700">{c.body}</p>
        </div>
        {c.status === "visible" && (
          <div className="mt-1.5 flex items-center gap-4 pl-2">
            <LikeButton type="comment" id={c.id} liked={c.liked} count={c.reaction_count} onChange={reload} />
            {canComment && !nested && (
              <button onClick={() => setReplyTo(replyTo === c.id ? null : c.id)} className="inline-flex items-center gap-1.5 text-[13px] font-medium text-slate-500 hover:text-navy">
                <Reply className="size-3.5" /> Reply
              </button>
            )}
            {user && c.author.id === user.id ? (
              <button
                onClick={async () => {
                  if (await confirm({ title: "Delete this comment?", confirmLabel: "Delete", destructive: true })) {
                    await del.mutateAsync(`/api/comments/${c.id}`);
                    reload();
                  }
                }}
                className="inline-flex items-center gap-1.5 text-[13px] font-medium text-slate-500 hover:text-red-600"
              >
                <Trash2 className="size-3.5" /> Delete
              </button>
            ) : (
              <ReportButton targetType="comment" targetId={c.id} />
            )}
          </div>
        )}
        {!nested && (
          <>
            {replies(c.id).length > 0 && <ul className="border-l-2 border-border pl-4">{replies(c.id).map((r) => renderComment(r, true))}</ul>}
            {replyTo === c.id && (
              <div className="mt-3 border-l-2 border-green-500 pl-4">
                <CommentForm discussionId={d.id} parentId={c.id} autoFocus onDone={() => { setReplyTo(null); reload(); }} />
              </div>
            )}
          </>
        )}
      </div>
    </li>
  );

  return (
    <div className="container max-w-3xl py-10">
      <Seo title={d.title} description={d.body.slice(0, 150)} />
      <Link to="/community" className="inline-flex items-center gap-1.5 text-sm font-semibold text-green-600 hover:gap-2.5"><ArrowLeft className="size-4" /> Community</Link>

      <article className="mt-6 rounded-2xl border border-border bg-white p-5 shadow-card sm:p-8">
        <div className="mb-3 flex flex-wrap gap-1.5">
          {d.is_pinned && <Badge variant="navy"><Pin /> Pinned</Badge>}
          <Badge variant="outline">{d.category.name}</Badge>
          {d.area_council && <Badge variant="outline">{d.area_council.name}</Badge>}
          <Badge variant="outline">User-generated content</Badge>
          {d.is_locked && <Badge variant="danger"><Lock /> Closed</Badge>}
        </div>
        <h1 className="text-2xl font-extrabold leading-tight sm:text-3xl">{d.title}</h1>
        <div className="mt-4 flex items-center gap-3">
          <Avatar name={d.author.name} team={d.author.is_team} />
          <p className="text-sm">
            <span className="font-semibold text-navy">{d.author.name}</span>
            {d.author.is_team && <span className="ml-1.5 text-xs font-semibold text-green-600">NIPAM Team</span>}
            <span className="block text-xs text-slate-500">{timeAgo(d.created_at)}</span>
          </p>
        </div>
        <Markdown className="mt-5 text-base">{d.body}</Markdown>
        <div className="mt-6 flex flex-wrap items-center gap-5 border-t border-border pt-4">
          <LikeButton type="discussion" id={d.id} liked={d.liked} count={d.reaction_count} onChange={reload} />
          <span className="inline-flex items-center gap-1.5 text-[13px] text-slate-500"><MessageSquare className="size-4" /> {d.comment_count} comments</span>
          <span className="ml-auto flex items-center gap-4">
            {d.can_edit ? (
              <button
                onClick={async () => {
                  if (await confirm({ title: "Delete this discussion?", description: "This cannot be undone.", confirmLabel: "Delete", destructive: true })) {
                    await del.mutateAsync(`/api/discussions/${d.id}`);
                    toast.success("Discussion deleted");
                    qc.invalidateQueries({ queryKey: ["discussions"] });
                    navigate("/community");
                  }
                }}
                className="inline-flex items-center gap-1.5 text-[13px] font-medium text-slate-500 hover:text-red-600"
              >
                <Trash2 className="size-3.5" /> Delete
              </button>
            ) : (
              <ReportButton targetType="discussion" targetId={d.id} />
            )}
          </span>
        </div>
      </article>

      <section className="mt-8" aria-labelledby="comments-heading">
        <h2 id="comments-heading" className="mb-5 text-xl font-extrabold">Comments ({d.comment_count})</h2>
        <div className="mb-8">
          {canComment ? (
            <CommentForm discussionId={d.id} onDone={reload} />
          ) : d.is_locked ? (
            <p className="rounded-xl bg-surface p-4 text-sm text-muted-foreground">This discussion is closed to new comments.</p>
          ) : !user ? (
            <p className="rounded-xl bg-surface p-4 text-sm text-muted-foreground">
              <Link to={`/login?next=${encodeURIComponent(location.pathname)}`} className="font-semibold text-green-600">Log in</Link> or <Link to="/join" className="font-semibold text-green-600">join NIPAM</Link> to comment.
            </p>
          ) : (
            <p className="rounded-xl bg-surface p-4 text-sm text-muted-foreground">
              <Link to="/settings?tab=verification" className="font-semibold text-green-600">Verify your email</Link> to join the conversation.
            </p>
          )}
        </div>
        {roots.length ? <ul className="space-y-5">{roots.map((c) => renderComment(c))}</ul> : <p className="text-sm text-muted-foreground">No comments yet. Start the conversation.</p>}
      </section>
    </div>
  );
}
