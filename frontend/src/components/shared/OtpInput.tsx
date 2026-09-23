import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export function OtpInput({ id, value, onChange, className, invalid }: { id: string; value: string; onChange: (v: string) => void; className?: string; invalid?: boolean }) {
  return (
    <Input
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value.replace(/\D/g, "").slice(0, 6))}
      inputMode="numeric"
      autoComplete="one-time-code"
      pattern="[0-9]{6}"
      maxLength={6}
      placeholder="••••••"
      aria-invalid={invalid || undefined}
      className={cn("h-14 text-center font-display text-2xl font-bold tracking-[0.6em] placeholder:tracking-[0.6em]", className)}
    />
  );
}

/** Development helper: shows OTP codes returned by the API when no email/SMS
 * provider is connected (NIPAM_DEV_EXPOSE_OTP). Never shown in production. */
export function DevCode({ code, label }: { code?: string; label: string }) {
  if (!code) return null;
  return (
    <p className="rounded-xl bg-amber-50 px-4 py-2.5 text-sm text-amber-900 ring-1 ring-amber-200">
      <strong>Development mode:</strong> {label} code is <code className="font-bold tracking-widest">{code}</code>
    </p>
  );
}
