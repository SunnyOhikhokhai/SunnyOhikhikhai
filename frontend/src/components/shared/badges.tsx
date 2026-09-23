import { AlertTriangle, BadgeCheck, CircleDashed, Clock, FlaskConical } from "lucide-react";
import { CONTENT_LABELS, VERIFICATION } from "@/lib/constants";
import type { ContentLabel, VerificationStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const V_ICONS = { verified: BadgeCheck, pending_review: Clock, unverified: CircleDashed, disputed: AlertTriangle };

export function VerificationBadge({ status, className }: { status: VerificationStatus; className?: string }) {
  const v = VERIFICATION[status];
  const Icon = V_ICONS[status];
  return (
    <span
      className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset", v.tone, className)}
      title={v.description}
    >
      <Icon className="size-3.5" aria-hidden />
      {v.label}
    </span>
  );
}

export function ContentLabelBadge({ label, className }: { label: ContentLabel; className?: string }) {
  const c = CONTENT_LABELS[label] ?? CONTENT_LABELS.update;
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset", c.tone, className)}>
      {c.label}
    </span>
  );
}

export function DemoBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn("inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-800 ring-1 ring-inset ring-amber-600/30", className)}
      title="Sample content for demonstration — not verified information"
    >
      <FlaskConical className="size-3" aria-hidden />
      Sample
    </span>
  );
}
