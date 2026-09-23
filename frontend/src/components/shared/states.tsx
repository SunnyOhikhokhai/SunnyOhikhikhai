import { AlertCircle, Inbox, RefreshCw, WifiOff } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";

export function EmptyState({
  title,
  description,
  action,
  icon: Icon = Inbox,
  className,
}: {
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  icon?: typeof Inbox;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center rounded-2xl border border-dashed border-silver-light bg-surface/60 px-6 py-14 text-center", className)}>
      <div className="flex size-14 items-center justify-center rounded-2xl bg-white text-navy-400 shadow-card">
        <Icon className="size-7" strokeWidth={1.6} />
      </div>
      <h3 className="mt-4 text-lg font-bold">{title}</h3>
      {description && <p className="mt-1.5 max-w-md text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ErrorState({ error, onRetry, className }: { error: unknown; onRetry?: () => void; className?: string }) {
  const offline = error instanceof ApiError && error.code === "network_error";
  const message = error instanceof Error ? error.message : "Something went wrong.";
  return (
    <div role="alert" className={cn("flex flex-col items-center rounded-2xl border border-red-100 bg-red-50/50 px-6 py-12 text-center", className)}>
      {offline ? <WifiOff className="size-8 text-red-500" /> : <AlertCircle className="size-8 text-red-500" />}
      <h3 className="mt-3 text-lg font-bold">{offline ? "You're offline" : "We couldn't load this"}</h3>
      <p className="mt-1 max-w-md text-sm text-slate-600">{message}</p>
      {onRetry && (
        <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>
          <RefreshCw /> Try again
        </Button>
      )}
    </div>
  );
}
