import { useMutation } from "@tanstack/react-query";
import { Flag } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { REPORT_REASONS } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function ReportButton({ targetType, targetId, className }: { targetType: "discussion" | "comment"; targetId: number; className?: string }) {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<string>("");
  const [details, setDetails] = useState("");
  const m = useMutation({
    mutationFn: () => api.post("/api/reports", { target_type: targetType, target_id: targetId, reason, details: details || null }),
    onSuccess: () => {
      toast.success("Thank you. A moderator will review this report.");
      setOpen(false);
      setReason("");
      setDetails("");
    },
    onError: (e: Error) => toast.error(e.message),
  });
  if (!user) return null;
  return (
    <>
      <button onClick={() => setOpen(true)} className={cn("inline-flex items-center gap-1.5 text-[13px] font-medium text-slate-500 hover:text-red-600", className)}>
        <Flag className="size-3.5" /> Report
      </button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Report this {targetType}</DialogTitle>
            <DialogDescription>Reports are confidential. Tell us which community guideline this breaks.</DialogDescription>
          </DialogHeader>
          <fieldset className="grid gap-2">
            <legend className="sr-only">Reason</legend>
            {REPORT_REASONS.map(([value, label]) => (
              <label key={value} className={cn("flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-2.5 text-sm transition", reason === value ? "border-green-500 bg-green-50 font-semibold text-navy" : "border-border hover:border-navy-200")}>
                <input type="radio" name="reason" value={value} checked={reason === value} onChange={() => setReason(value)} className="accent-green-600" />
                {label}
              </label>
            ))}
          </fieldset>
          <div className="mt-4 space-y-1.5">
            <Label htmlFor="report-details">Additional details <span className="font-normal text-muted-foreground">(optional)</span></Label>
            <Textarea id="report-details" value={details} onChange={(e) => setDetails(e.target.value)} maxLength={1000} className="min-h-[80px]" />
          </div>
          <div className="mt-5 flex justify-end gap-2">
            <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button variant="destructive" disabled={!reason} loading={m.isPending} onClick={() => m.mutate()}>Submit report</Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
