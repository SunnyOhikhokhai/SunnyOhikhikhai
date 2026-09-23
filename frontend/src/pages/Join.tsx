import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Check, CheckCircle2, Info, Mail, MapPin, ShieldCheck, Smartphone } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { AuthShell } from "@/components/layout/AuthShell";
import { DevCode, OtpInput } from "@/components/shared/OtpInput";
import { PasswordInput, PasswordStrength, passwordChecks } from "@/components/shared/PasswordInput";
import { Seo } from "@/components/shared/Seo";
import { Button } from "@/components/ui/button";
import { Checkbox, Switch } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Field, Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { useMeta } from "@/hooks/useMeta";
import { api, ApiError } from "@/lib/api";
import type { Me } from "@/lib/types";
import { cn } from "@/lib/utils";

const STEPS = ["Personal information", "Location", "Verification", "Consent"];

function Stepper({ step }: { step: number }) {
  return (
    <ol className="mb-8 grid grid-cols-4 gap-2" aria-label="Registration progress">
      {STEPS.map((label, i) => {
        const done = i < step;
        const current = i === step;
        return (
          <li key={label} aria-current={current ? "step" : undefined}>
            <div className={cn("h-1.5 rounded-full transition-colors", done || current ? "bg-green-500" : "bg-silver-light/70")} />
            <p className={cn("mt-2 text-[11px] font-semibold uppercase tracking-wider sm:text-xs", current ? "text-navy" : done ? "text-green-700" : "text-slate-400")}>
              <span className="sr-only">Step {i + 1}: </span>
              {done && <Check className="mr-0.5 inline size-3" />}
              <span className={cn(!current && "hidden sm:inline")}>{label}</span>
              {!current && <span className="sm:hidden">{i + 1}</span>}
            </p>
          </li>
        );
      })}
    </ol>
  );
}

interface FormState {
  full_name: string;
  email: string;
  phone: string;
  password: string;
  confirm: string;
  area_council: string;
  ward: string;
  community: string;
  accept_terms: boolean;
}

export default function Join() {
  const { user, setUser, smsEnabled, refresh } = useAuth();
  const navigate = useNavigate();
  const meta = useMeta();
  const inFlow = useRef(false);
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormState>({ full_name: "", email: "", phone: "", password: "", confirm: "", area_council: "", ward: "", community: "", accept_terms: false });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [devCodes, setDevCodes] = useState<Record<string, string>>({});
  const [emailCode, setEmailCode] = useState("");
  const [smsCode, setSmsCode] = useState("");
  const [consent, setConsent] = useState({ events_email: false, events_sms: false, announcements_email: false, announcements_sms: false });

  // Returning, logged-in members: resume verification or go to the dashboard.
  useEffect(() => {
    if (!user || inFlow.current) return;
    if (!user.email_verified) {
      inFlow.current = true;
      setStep(2);
    } else navigate("/dashboard", { replace: true });
  }, [user, navigate]);

  const set = (k: keyof FormState, v: string | boolean) => setForm((f) => ({ ...f, [k]: v }));
  const top = () => window.scrollTo({ top: 0, behavior: "smooth" });

  const validateStep1 = () => {
    const e: Record<string, string> = {};
    if (form.full_name.trim().length < 2) e.full_name = "Enter your full name.";
    if (!/^\S+@\S+\.\S+$/.test(form.email)) e.email = "Enter a valid email address.";
    if (form.phone && !/^\+?[\d\s\-()]{10,17}$/.test(form.phone)) e.phone = "Enter a valid phone number, e.g. 0803 000 0000.";
    if (!passwordChecks(form.password).every((c) => c.ok)) e.password = "Choose a stronger password.";
    if (form.password !== form.confirm) e.confirm = "Passwords do not match.";
    setErrors(e);
    return !Object.keys(e).length;
  };

  const register = useMutation({
    mutationFn: () =>
      api.post<{ data: { user: Me; dev_codes?: Record<string, string> } }>("/api/auth/register", {
        full_name: form.full_name,
        email: form.email,
        phone: form.phone || null,
        password: form.password,
        area_council: form.area_council,
        ward: form.ward || null,
        community: form.community || null,
        accept_terms: form.accept_terms,
        consent_event_notifications: false,
        consent_announcements: false,
      }),
    onSuccess: (res) => {
      inFlow.current = true;
      setUser(res.data.user);
      setDevCodes(res.data.dev_codes ?? {});
      setStep(2);
      top();
      toast.success("Account created. Check your email for a verification code.");
    },
    onError: (e: Error) => {
      if (e instanceof ApiError && e.fields) setErrors(e.fields);
      if (e instanceof ApiError && ["account_exists", "weak_password"].includes(e.code)) setStep(0);
      toast.error(e.message);
    },
  });

  const confirmCode = useMutation({
    mutationFn: ({ channel, code }: { channel: "email" | "sms"; code: string }) => api.post<{ data: { user: Me } }>("/api/auth/verify/confirm", { channel, code }),
    onSuccess: (res, v) => {
      setUser(res.data.user);
      toast.success(v.channel === "email" ? "Email verified" : "Phone number verified");
    },
    onError: (e: Error) => toast.error(e.message),
  });
  const resend = useMutation({
    mutationFn: (channel: "email" | "sms") => api.post<{ data: { dev_codes?: Record<string, string> } }>("/api/auth/verify/request", { channel }),
    onSuccess: (res) => {
      setDevCodes((d) => ({ ...d, ...(res.data.dev_codes ?? {}) }));
      toast.success("A new code has been sent.");
    },
    onError: (e: Error) => toast.error(e.message),
  });
  const savePrefs = useMutation({
    mutationFn: () =>
      api.put("/api/users/me/preferences", {
        email_events: consent.events_email,
        sms_events: consent.events_sms,
        email_announcements: consent.announcements_email,
        sms_announcements: consent.announcements_sms,
      }),
    onSuccess: async () => {
      await refresh();
      toast.success(`Welcome to NIPAM, ${user?.first_name ?? ""}!`);
      navigate("/dashboard");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const hasPhone = !!(user?.phone ?? form.phone);

  return (
    <>
      <Seo title="Join NIPAM" description="Create your free NIPAM account in four simple steps." />
      <AuthShell
        title={["Create your account", "Where do you live?", "Verify your account", "Your communication choices"][step]}
        subtitle={
          step === 0 ? (
            <>Already a member? <Link to="/login" className="font-semibold text-green-600 hover:underline">Log in</Link></>
          ) : step === 1 ? (
            "Choose the FCT Area Council you reside in."
          ) : step === 2 ? (
            "We've sent a 6-digit code to confirm your details."
          ) : (
            "You decide what we send you. You can change this any time."
          )
        }
      >
        <Stepper step={step} />

        {step === 0 && (
          <form
            noValidate
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              if (validateStep1()) {
                setStep(1);
                top();
              }
            }}
          >
            <Field id="full_name" label="Full name" error={errors.full_name}>
              <Input autoComplete="name" value={form.full_name} onChange={(e) => set("full_name", e.target.value)} required />
            </Field>
            <Field id="email" label="Email address" error={errors.email}>
              <Input type="email" autoComplete="email" value={form.email} onChange={(e) => set("email", e.target.value)} required />
            </Field>
            <Field id="phone" label="Phone number" optional error={errors.phone} hint="Used for account verification and SMS alerts you choose. Never shown publicly.">
              <Input type="tel" autoComplete="tel" inputMode="tel" placeholder="0803 000 0000" value={form.phone} onChange={(e) => set("phone", e.target.value)} />
            </Field>
            <Field id="password" label="Password" error={errors.password}>
              <PasswordInput autoComplete="new-password" value={form.password} onChange={(e) => set("password", e.target.value)} required />
            </Field>
            {form.password && <PasswordStrength password={form.password} />}
            <Field id="confirm" label="Confirm password" error={errors.confirm}>
              <PasswordInput autoComplete="new-password" value={form.confirm} onChange={(e) => set("confirm", e.target.value)} required />
            </Field>
            <Button type="submit" size="lg" className="w-full">
              Continue <ArrowRight />
            </Button>
          </form>
        )}

        {step === 1 && (
          <form
            className="space-y-5"
            onSubmit={(e) => {
              e.preventDefault();
              if (!form.area_council) return setErrors({ area_council: "Please choose your Area Council." });
              if (!form.accept_terms) return setErrors({ accept_terms: "Please accept the Terms of Use and Privacy Policy." });
              setErrors({});
              register.mutate();
            }}
          >
            <fieldset>
              <legend className="mb-3 text-sm font-semibold text-navy-900">Which FCT Area Council do you reside in?</legend>
              <div className="grid grid-cols-2 gap-2.5">
                {meta.data?.area_councils.map((c) => (
                  <label
                    key={c.slug}
                    className={cn(
                      "flex cursor-pointer items-center gap-2.5 rounded-xl border-2 p-3.5 transition focus-within:ring-2 focus-within:ring-green-500",
                      form.area_council === c.slug ? "border-green-500 bg-green-50" : "border-border hover:border-navy-200",
                    )}
                  >
                    <input type="radio" name="area_council" value={c.slug} checked={form.area_council === c.slug} onChange={() => set("area_council", c.slug)} className="sr-only" />
                    <MapPin className={cn("size-4 shrink-0", form.area_council === c.slug ? "text-green-600" : "text-slate-400")} />
                    <span>
                      <span className="block text-sm font-bold text-navy">{c.short_name}</span>
                      <span className="block text-[11px] leading-tight text-muted-foreground">{c.name}</span>
                    </span>
                  </label>
                ))}
              </div>
              {errors.area_council && <p role="alert" className="mt-2 text-[13px] font-medium text-red-600">{errors.area_council}</p>}
            </fieldset>
            <p className="flex gap-2 rounded-xl bg-surface p-3.5 text-[13px] text-slate-600 ring-1 ring-border">
              <Info className="mt-0.5 size-4 shrink-0 text-navy-400" />
              Your Area Council personalises the updates you see. It is self-declared and is not a statement of electoral eligibility or voting location.
            </p>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field id="ward" label="Ward" optional>
                <Input value={form.ward} onChange={(e) => set("ward", e.target.value)} maxLength={120} />
              </Field>
              <Field id="community" label="Community" optional>
                <Input value={form.community} onChange={(e) => set("community", e.target.value)} maxLength={120} />
              </Field>
            </div>
            <div>
              <label className="flex items-start gap-3 text-sm text-slate-700">
                <Checkbox checked={form.accept_terms} onCheckedChange={(v) => set("accept_terms", v === true)} aria-invalid={!!errors.accept_terms} />
                <span>
                  I have read and accept the <Link to="/terms" target="_blank" className="font-semibold text-green-600 underline-offset-2 hover:underline">Terms of Use</Link>,{" "}
                  <Link to="/privacy" target="_blank" className="font-semibold text-green-600 underline-offset-2 hover:underline">Privacy Policy</Link> and{" "}
                  <Link to="/community-guidelines" target="_blank" className="font-semibold text-green-600 underline-offset-2 hover:underline">Community Guidelines</Link>.
                </span>
              </label>
              {errors.accept_terms && <p role="alert" className="mt-2 text-[13px] font-medium text-red-600">{errors.accept_terms}</p>}
            </div>
            <div className="flex gap-3">
              <Button type="button" variant="outline" size="lg" onClick={() => setStep(0)}>
                <ArrowLeft /> Back
              </Button>
              <Button type="submit" size="lg" className="flex-1" loading={register.isPending}>
                Create account <ArrowRight />
              </Button>
            </div>
          </form>
        )}

        {step === 2 && user && (
          <div className="space-y-6">
            <section className="rounded-2xl border border-border p-5">
              <div className="flex items-center gap-3">
                <span className={cn("flex size-10 items-center justify-center rounded-xl", user.email_verified ? "bg-green-100 text-green-700" : "bg-navy-50 text-navy")}>
                  {user.email_verified ? <CheckCircle2 className="size-5" /> : <Mail className="size-5" />}
                </span>
                <div className="min-w-0">
                  <p className="font-semibold text-navy">Email verification</p>
                  <p className="truncate text-sm text-muted-foreground">{user.email}</p>
                </div>
              </div>
              {!user.email_verified && (
                <form
                  className="mt-4 space-y-3"
                  onSubmit={(e) => {
                    e.preventDefault();
                    confirmCode.mutate({ channel: "email", code: emailCode });
                  }}
                >
                  <DevCode code={devCodes.email} label="Email" />
                  <Label htmlFor="email-code">Enter the 6-digit code</Label>
                  <OtpInput id="email-code" value={emailCode} onChange={setEmailCode} />
                  <div className="flex items-center justify-between">
                    <button type="button" className="text-sm font-semibold text-green-600 hover:underline disabled:opacity-50" disabled={resend.isPending} onClick={() => resend.mutate("email")}>
                      Resend code
                    </button>
                    <Button type="submit" disabled={emailCode.length !== 6} loading={confirmCode.isPending}>Verify email</Button>
                  </div>
                </form>
              )}
            </section>

            <section className="rounded-2xl border border-border p-5">
              <div className="flex items-center gap-3">
                <span className={cn("flex size-10 items-center justify-center rounded-xl", user.phone_verified ? "bg-green-100 text-green-700" : "bg-navy-50 text-navy")}>
                  {user.phone_verified ? <CheckCircle2 className="size-5" /> : <Smartphone className="size-5" />}
                </span>
                <div>
                  <p className="font-semibold text-navy">Phone verification</p>
                  <p className="text-sm text-muted-foreground">{user.phone ?? "No phone number added"}</p>
                </div>
              </div>
              {user.phone && !user.phone_verified && (
                smsEnabled ? (
                  <form className="mt-4 space-y-3" onSubmit={(e) => { e.preventDefault(); confirmCode.mutate({ channel: "sms", code: smsCode }); }}>
                    <DevCode code={devCodes.sms} label="SMS" />
                    <Label htmlFor="sms-code">Enter the code sent by SMS</Label>
                    <OtpInput id="sms-code" value={smsCode} onChange={setSmsCode} />
                    <div className="flex items-center justify-between">
                      <button type="button" className="text-sm font-semibold text-green-600 hover:underline" onClick={() => resend.mutate("sms")}>Resend SMS</button>
                      <Button type="submit" disabled={smsCode.length !== 6} loading={confirmCode.isPending}>Verify phone</Button>
                    </div>
                  </form>
                ) : (
                  <p className="mt-3 text-sm text-muted-foreground">SMS verification will be available once NIPAM connects an SMS provider. You can verify later from your settings.</p>
                )
              )}
            </section>

            <div className="flex flex-col gap-2">
              <Button size="lg" onClick={() => { setStep(3); top(); }} disabled={!user.email_verified}>
                Continue <ArrowRight />
              </Button>
              {!user.email_verified && (
                <button className="text-sm font-medium text-slate-500 hover:text-navy" onClick={() => { setStep(3); top(); }}>
                  Verify later — some features need a verified email
                </button>
              )}
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-5">
            <div className="flex items-start gap-3 rounded-2xl border border-border bg-surface p-4">
              <ShieldCheck className="mt-0.5 size-5 shrink-0 text-green-600" />
              <div className="flex-1">
                <p className="font-semibold text-navy">Account communications</p>
                <p className="text-sm text-muted-foreground">Security codes, password changes and essential account notices. Always on.</p>
              </div>
              <Switch checked disabled aria-label="Account communications (required)" />
            </div>
            {[
              { key: "events", title: "Event notifications", text: "New events and reminders for events you register for." },
              { key: "announcements", title: "Important platform announcements", text: "Official NIPAM announcements for the FCT and your Area Council." },
            ].map((row) => (
              <fieldset key={row.key} className="rounded-2xl border border-border p-4">
                <legend className="sr-only">{row.title}</legend>
                <p className="font-semibold text-navy">{row.title}</p>
                <p className="text-sm text-muted-foreground">{row.text}</p>
                <div className="mt-3 flex flex-wrap gap-5">
                  <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
                    <Checkbox
                      checked={consent[`${row.key}_email` as keyof typeof consent]}
                      onCheckedChange={(v) => setConsent((c) => ({ ...c, [`${row.key}_email`]: v === true }))}
                    />
                    By email
                  </label>
                  <label className={cn("flex items-center gap-2 text-sm font-medium", hasPhone ? "text-slate-700" : "text-slate-400")}>
                    <Checkbox
                      disabled={!hasPhone}
                      checked={consent[`${row.key}_sms` as keyof typeof consent]}
                      onCheckedChange={(v) => setConsent((c) => ({ ...c, [`${row.key}_sms`]: v === true }))}
                    />
                    By SMS {!smsEnabled && <span className="text-xs text-slate-400">(when available)</span>}
                  </label>
                </div>
              </fieldset>
            ))}
            <p className="text-[13px] text-muted-foreground">
              In-app notifications appear in your NIPAM notification centre. We never subscribe you to unrelated communications and never share your contact details.
            </p>
            <Button size="lg" className="w-full" loading={savePrefs.isPending} onClick={() => savePrefs.mutate()}>
              Finish and go to my dashboard <ArrowRight />
            </Button>
          </div>
        )}
      </AuthShell>
    </>
  );
}
