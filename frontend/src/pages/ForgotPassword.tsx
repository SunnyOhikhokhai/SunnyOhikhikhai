import { useMutation } from "@tanstack/react-query";
import { CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { AuthShell } from "@/components/layout/AuthShell";
import { DevCode, OtpInput } from "@/components/shared/OtpInput";
import { PasswordInput, PasswordStrength, passwordChecks } from "@/components/shared/PasswordInput";
import { Seo } from "@/components/shared/Seo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, Label } from "@/components/ui/label";
import { api } from "@/lib/api";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [devCode, setDevCode] = useState<string>();
  const request = useMutation({
    mutationFn: () => api.post<{ data: { dev_codes?: { reset?: string } } }>("/api/auth/password/forgot", { email }),
    onSuccess: (r) => {
      setSent(true);
      setDevCode(r.data.dev_codes?.reset);
    },
    onError: (e: Error) => toast.error(e.message),
  });
  const reset = useMutation({
    mutationFn: () => api.post("/api/auth/password/reset", { email, code, password }),
    onSuccess: () => {
      toast.success("Password updated. All other sessions have been signed out. Please log in.");
      navigate("/login");
    },
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <>
      <Seo title="Reset password" noindex />
      <AuthShell title="Reset your password" subtitle={<>Remembered it? <Link to="/login" className="font-semibold text-green-600 hover:underline">Back to login</Link></>}>
        {!sent ? (
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); request.mutate(); }}>
            <Field id="email" label="Email address" hint="We'll send a 6-digit reset code if an account exists.">
              <Input type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </Field>
            <Button type="submit" size="lg" className="w-full" loading={request.isPending}>Send reset code</Button>
          </form>
        ) : (
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); reset.mutate(); }}>
            <p className="flex gap-2 rounded-xl bg-green-50 p-4 text-sm text-green-800 ring-1 ring-green-200">
              <CheckCircle2 className="size-5 shrink-0" /> If an account exists for {email}, a reset code is on its way.
            </p>
            <DevCode code={devCode} label="Reset" />
            <Label htmlFor="code">Reset code</Label>
            <OtpInput id="code" value={code} onChange={setCode} />
            <Field id="new-password" label="New password">
              <PasswordInput autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </Field>
            {password && <PasswordStrength password={password} />}
            <Button type="submit" size="lg" className="w-full" loading={reset.isPending} disabled={code.length !== 6 || !passwordChecks(password).every((c) => c.ok)}>
              Update password
            </Button>
          </form>
        )}
      </AuthShell>
    </>
  );
}
