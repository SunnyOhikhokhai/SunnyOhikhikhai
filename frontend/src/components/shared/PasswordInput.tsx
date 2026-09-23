import { Eye, EyeOff } from "lucide-react";
import { forwardRef, useState } from "react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export const PasswordInput = forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(({ className, ...props }, ref) => {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <Input ref={ref} type={show ? "text" : "password"} className={cn("pr-11", className)} {...props} />
      <button type="button" onClick={() => setShow((s) => !s)} className="absolute right-1 top-1/2 -translate-y-1/2 rounded-lg p-2 text-slate-400 hover:text-navy" aria-label={show ? "Hide password" : "Show password"}>
        {show ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
      </button>
    </div>
  );
});
PasswordInput.displayName = "PasswordInput";

export function passwordChecks(pw: string) {
  return [
    { ok: pw.length >= 10, label: "At least 10 characters" },
    { ok: /[a-z]/.test(pw) && /[A-Z]/.test(pw), label: "Upper and lower case letters" },
    { ok: /\d/.test(pw), label: "A number" },
  ];
}

export function PasswordStrength({ password }: { password: string }) {
  const checks = passwordChecks(password);
  const score = checks.filter((c) => c.ok).length + (password.length >= 14 ? 1 : 0);
  const colors = ["bg-silver-light", "bg-red-500", "bg-amber-500", "bg-green-500", "bg-green-600"];
  return (
    <div className="space-y-2" aria-live="polite">
      <div className="flex gap-1">
        {[1, 2, 3, 4].map((i) => (
          <span key={i} className={cn("h-1.5 flex-1 rounded-full transition-colors", score >= i ? colors[score] : "bg-silver-light/60")} />
        ))}
      </div>
      <ul className="grid gap-1 text-[13px] sm:grid-cols-3">
        {checks.map((c) => (
          <li key={c.label} className={c.ok ? "text-green-700" : "text-slate-500"}>
            {c.ok ? "✓" : "○"} {c.label}
          </li>
        ))}
      </ul>
    </div>
  );
}
