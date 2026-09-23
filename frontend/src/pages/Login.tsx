import { useMutation } from "@tanstack/react-query";
import { KeyRound, LogIn, MessageSquareCode } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { AuthShell } from "@/components/layout/AuthShell";
import { DevCode, OtpInput } from "@/components/shared/OtpInput";
import { PasswordInput } from "@/components/shared/PasswordInput";
import { Seo } from "@/components/shared/Seo";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Field, Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import type { Me } from "@/lib/types";
import { cn } from "@/lib/utils";

function safeNext(next: string | null) {
  return next && next.startsWith("/") && !next.startsWith("//") ? next : null;
}

export default function Login() {
  const { setUser, smsEnabled } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [mode, setMode] = useState<"password" | "otp">("password");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [channel, setChannel] = useState<"email" | "sms">("email");
  const [code, setCode] = useState("");
  const [devCode, setDevCode] = useState<string>();
  const [error, setError] = useState<string>();

  const done = (user: Me) => {
    setUser(user);
    toast.success(`Welcome back, ${user.first_name}.`);
    navigate(safeNext(params.get("next")) ?? (user.admin ? "/admin" : "/dashboard"), { replace: true });
  };

  const login = useMutation({
    mutationFn: () => api.post<{ data: { user: Me } }>("/api/auth/login", { identifier, password, remember_me: remember }),
    onSuccess: (r) => done(r.data.user),
    onError: (e: Error) => setError(e.message),
  });
  const requestOtp = useMutation({
    mutationFn: () => api.post<{ data: { dev_codes?: { login?: string } } }>("/api/auth/otp/request", { identifier, channel }),
    onSuccess: (r) => {
      setOtpSent(true);
      setDevCode(r.data.dev_codes?.login);
      toast.success("If an account exists, a login code has been sent.");
    },
    onError: (e: Error) => setError(e.message),
  });
  const verifyOtp = useMutation({
    mutationFn: () => api.post<{ data: { user: Me } }>("/api/auth/otp/verify", { identifier, channel, code, remember_me: remember }),
    onSuccess: (r) => done(r.data.user),
    onError: (e: Error) => setError(e.message),
  });

  return (
    <>
      <Seo title="Login" description="Log in to your NIPAM member account." noindex />
      <AuthShell title="Welcome back" subtitle={<>New to NIPAM? <Link to="/join" className="font-semibold text-green-600 hover:underline">Create a free account</Link></>}>
        <div className="mb-6 grid grid-cols-2 rounded-xl bg-surface p-1 ring-1 ring-border" role="tablist" aria-label="Login method">
          {([["password", "Password", KeyRound], ["otp", "One-time code", MessageSquareCode]] as const).map(([k, label, Icon]) => (
            <button
              key={k}
              role="tab"
              aria-selected={mode === k}
              onClick={() => { setMode(k); setError(undefined); }}
              className={cn("flex items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-semibold transition", mode === k ? "bg-white text-navy shadow-card" : "text-slate-500 hover:text-navy")}
            >
              <Icon className="size-4" /> {label}
            </button>
          ))}
        </div>

        {error && <p role="alert" className="mb-4 rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700 ring-1 ring-red-200">{error}</p>}

        {mode === "password" ? (
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); setError(undefined); login.mutate(); }}>
            <Field id="identifier" label="Email or phone number">
              <Input autoComplete="username" value={identifier} onChange={(e) => setIdentifier(e.target.value)} required />
            </Field>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link to="/forgot-password" className="text-sm font-semibold text-green-600 hover:underline">Forgot password?</Link>
              </div>
              <PasswordInput id="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <label className="flex items-center gap-2.5 text-sm text-slate-700">
              <Checkbox checked={remember} onCheckedChange={(v) => setRemember(v === true)} /> Remember me on this device
            </label>
            <Button type="submit" size="lg" className="w-full" loading={login.isPending}><LogIn /> Log in</Button>
          </form>
        ) : !otpSent ? (
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); setError(undefined); requestOtp.mutate(); }}>
            <Field id="otp-identifier" label="Email or phone number">
              <Input autoComplete="username" value={identifier} onChange={(e) => setIdentifier(e.target.value)} required />
            </Field>
            <fieldset className="space-y-2">
              <legend className="text-sm font-semibold text-navy-900">Send my code by</legend>
              <div className="flex gap-3">
                {(["email", "sms"] as const).map((c) => (
                  <label key={c} className={cn("flex flex-1 cursor-pointer items-center justify-center gap-2 rounded-xl border-2 py-2.5 text-sm font-semibold", channel === c ? "border-green-500 bg-green-50 text-navy" : "border-border text-slate-600", c === "sms" && !smsEnabled && "cursor-not-allowed opacity-50")}>
                    <input type="radio" className="sr-only" name="channel" checked={channel === c} disabled={c === "sms" && !smsEnabled} onChange={() => setChannel(c)} />
                    {c === "email" ? "Email" : "SMS"}
                  </label>
                ))}
              </div>
              {!smsEnabled && <p className="text-xs text-muted-foreground">SMS codes become available once an SMS provider is connected.</p>}
            </fieldset>
            <Button type="submit" size="lg" className="w-full" loading={requestOtp.isPending}>Send login code</Button>
          </form>
        ) : (
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); setError(undefined); verifyOtp.mutate(); }}>
            <DevCode code={devCode} label="Login" />
            <Label htmlFor="otp">Enter the 6-digit code</Label>
            <OtpInput id="otp" value={code} onChange={setCode} />
            <label className="flex items-center gap-2.5 text-sm text-slate-700">
              <Checkbox checked={remember} onCheckedChange={(v) => setRemember(v === true)} /> Remember me on this device
            </label>
            <Button type="submit" size="lg" className="w-full" disabled={code.length !== 6} loading={verifyOtp.isPending}>Verify and log in</Button>
            <button type="button" className="w-full text-sm font-semibold text-green-600 hover:underline" onClick={() => { setOtpSent(false); setCode(""); }}>
              Use a different email/phone or resend
            </button>
          </form>
        )}
        <p className="mt-8 text-center text-xs text-muted-foreground">
          Protected by secure sessions. Never share your password or one-time codes — NIPAM staff will never ask for them.
        </p>
      </AuthShell>
    </>
  );
}
