import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCircle2, KeyRound, Mail, ShieldAlert, Smartphone, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { DevCode, OtpInput } from "@/components/shared/OtpInput";
import { PageHeader } from "@/components/shared/PageHeader";
import { PasswordInput, PasswordStrength, passwordChecks } from "@/components/shared/PasswordInput";
import { Seo } from "@/components/shared/Seo";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/checkbox";
import { useConfirm } from "@/components/ui/confirm";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input, Select, Textarea } from "@/components/ui/input";
import { Field, Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/hooks/useAuth";
import { useMeta } from "@/hooks/useMeta";
import { api, ApiError, getData } from "@/lib/api";
import type { Me, Preferences } from "@/lib/types";
import { cn } from "@/lib/utils";

function Section({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-border bg-white p-5 shadow-card sm:p-7">
      <h2 className="text-lg font-extrabold">{title}</h2>
      {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      <div className="mt-6">{children}</div>
    </section>
  );
}

function ProfileTab({ user }: { user: Me }) {
  const { setUser } = useAuth();
  const meta = useMeta();
  const [f, setF] = useState({
    full_name: user.full_name,
    display_name: user.profile.display_name ?? "",
    bio: user.profile.bio ?? "",
    phone: user.phone ?? "",
    area_council: user.area_council?.slug ?? "",
    ward: user.profile.ward ?? "",
    community: user.profile.community ?? "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const m = useMutation({
    mutationFn: () => api.patch<{ data: Me }>("/api/users/me", { ...f, phone: f.phone || null }),
    onSuccess: (r) => {
      setUser(r.data);
      toast.success("Profile updated");
    },
    onError: (e: Error) => {
      if (e instanceof ApiError && e.fields) setErrors(e.fields);
      toast.error(e.message);
    },
  });
  return (
    <Section title="Profile" description="Your display name appears on community posts. Your email and phone number are never shown publicly.">
      <form className="grid gap-4 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); setErrors({}); m.mutate(); }}>
        <Field id="p-name" label="Full name" error={errors.full_name}><Input value={f.full_name} onChange={(e) => setF({ ...f, full_name: e.target.value })} required /></Field>
        <Field id="p-display" label="Display name" optional hint="Shown publicly instead of your full name."><Input value={f.display_name} onChange={(e) => setF({ ...f, display_name: e.target.value })} maxLength={80} /></Field>
        <Field id="p-email" label="Email address" hint="Contact NIPAM to change your email."><Input value={user.email} disabled /></Field>
        <Field id="p-phone" label="Phone number" optional error={errors.phone} hint="Changing it requires re-verification."><Input type="tel" value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} /></Field>
        <Field id="p-council" label="Area Council" hint="Self-declared. Not a statement of electoral eligibility.">
          <Select value={f.area_council} onChange={(e) => setF({ ...f, area_council: e.target.value })}>
            {meta.data?.area_councils.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}
          </Select>
        </Field>
        <Field id="p-ward" label="Ward" optional><Input value={f.ward} onChange={(e) => setF({ ...f, ward: e.target.value })} /></Field>
        <Field id="p-community" label="Community" optional><Input value={f.community} onChange={(e) => setF({ ...f, community: e.target.value })} /></Field>
        <Field id="p-bio" label="Short bio" optional className="sm:col-span-2"><Textarea value={f.bio} onChange={(e) => setF({ ...f, bio: e.target.value })} maxLength={500} className="min-h-[80px]" /></Field>
        <div className="sm:col-span-2"><Button type="submit" loading={m.isPending}>Save changes</Button></div>
      </form>
    </Section>
  );
}

function VerifyRow({ channel, user }: { channel: "email" | "sms"; user: Me }) {
  const { setUser, smsEnabled } = useAuth();
  const verified = channel === "email" ? user.email_verified : user.phone_verified;
  const target = channel === "email" ? user.email : user.phone;
  const [sent, setSent] = useState(false);
  const [code, setCode] = useState("");
  const [dev, setDev] = useState<string>();
  const request = useMutation({
    mutationFn: () => api.post<{ data: { dev_codes?: Record<string, string> } }>("/api/auth/verify/request", { channel }),
    onSuccess: (r) => { setSent(true); setDev(r.data.dev_codes?.[channel]); toast.success("Code sent"); },
    onError: (e: Error) => toast.error(e.message),
  });
  const confirm = useMutation({
    mutationFn: () => api.post<{ data: { user: Me } }>("/api/auth/verify/confirm", { channel, code }),
    onSuccess: (r) => { setUser(r.data.user); toast.success("Verified"); },
    onError: (e: Error) => toast.error(e.message),
  });
  const Icon = channel === "email" ? Mail : Smartphone;
  return (
    <div className="rounded-xl border border-border p-4">
      <div className="flex flex-wrap items-center gap-3">
        <Icon className="size-5 text-navy" />
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-navy">{channel === "email" ? "Email" : "Phone"}</p>
          <p className="truncate text-sm text-muted-foreground">{target ?? "Not provided"}</p>
        </div>
        {verified ? (
          <span className="flex items-center gap-1.5 text-sm font-semibold text-green-700"><CheckCircle2 className="size-4" /> Verified</span>
        ) : !target ? (
          <span className="text-sm text-muted-foreground">Add a phone number in Profile</span>
        ) : channel === "sms" && !smsEnabled ? (
          <span className="text-sm text-muted-foreground">SMS not yet available</span>
        ) : (
          <Button size="sm" variant="outline" onClick={() => request.mutate()} loading={request.isPending}>{sent ? "Resend code" : "Send code"}</Button>
        )}
      </div>
      {sent && !verified && (
        <form className="mt-4 space-y-3" onSubmit={(e) => { e.preventDefault(); confirm.mutate(); }}>
          <DevCode code={dev} label={channel === "email" ? "Email" : "SMS"} />
          <Label htmlFor={`v-${channel}`}>Enter the 6-digit code</Label>
          <div className="flex gap-2">
            <OtpInput id={`v-${channel}`} value={code} onChange={setCode} className="h-12 text-xl" />
            <Button type="submit" className="h-12" disabled={code.length !== 6} loading={confirm.isPending}>Verify</Button>
          </div>
        </form>
      )}
    </div>
  );
}

const PREF_ROWS: { title: string; description: string; keys: [keyof Preferences, string][] }[] = [
  { title: "Platform announcements", description: "Official NIPAM announcements for the FCT and your Area Council.", keys: [["in_app_announcements", "In-app"], ["email_announcements", "Email"], ["sms_announcements", "SMS"]] },
  { title: "Events", description: "New events and changes to events you've registered for.", keys: [["in_app_events", "In-app"], ["email_events", "Email"], ["sms_events", "SMS"]] },
  { title: "Community updates", description: "Replies to your discussions and comments.", keys: [["in_app_community", "In-app"], ["email_community", "Email"]] },
  { title: "Area Council updates", description: "News published for your Area Council.", keys: [["in_app_council_updates", "In-app"]] },
];

function NotificationsTab({ user }: { user: Me }) {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["preferences"], queryFn: () => getData<Preferences>("/api/users/me/preferences") });
  const m = useMutation({
    mutationFn: (patch: Partial<Preferences>) => api.put<{ data: Preferences }>("/api/users/me/preferences", patch),
    onMutate: (patch) => qc.setQueryData(["preferences"], (old: Preferences) => ({ ...old, ...patch })),
    onSuccess: (r) => { qc.setQueryData(["preferences"], r.data); toast.success("Preferences saved"); },
    onError: (e: Error) => { toast.error(e.message); qc.invalidateQueries({ queryKey: ["preferences"] }); },
  });
  if (!data) return <Skeleton className="h-80" />;
  return (
    <Section title="Communication preferences" description="Choose how NIPAM contacts you. Account and security messages are essential and always sent.">
      <div className="divide-y divide-border">
        {PREF_ROWS.map((row) => (
          <div key={row.title} className="grid gap-3 py-5 first:pt-0 last:pb-0 sm:grid-cols-[1fr_auto] sm:items-center">
            <div>
              <p className="font-semibold text-navy">{row.title}</p>
              <p className="text-sm text-muted-foreground">{row.description}</p>
            </div>
            <div className="flex gap-5">
              {row.keys.map(([key, label]) => {
                const smsBlocked = key.startsWith("sms_") && (!data.sms_enabled || !user.phone_verified);
                const emailBlocked = key.startsWith("email_") && !user.email_verified;
                const id = `pref-${key}`;
                return (
                  <div key={key} className="flex flex-col items-center gap-1.5">
                    <Switch id={id} checked={!!data[key]} disabled={smsBlocked || emailBlocked || m.isPending} onCheckedChange={(v) => m.mutate({ [key]: v })} />
                    <label htmlFor={id} className={cn("text-xs font-medium", smsBlocked || emailBlocked ? "text-slate-400" : "text-slate-600")}>{label}</label>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      <p className="mt-6 rounded-xl bg-surface p-4 text-xs text-muted-foreground">
        {!data.sms_enabled ? "SMS delivery will be enabled once NIPAM connects an approved SMS provider. " : !user.phone_verified ? "Verify your phone number to enable SMS. " : ""}
        Email options require a verified email address. We never share your contact details.
      </p>
    </Section>
  );
}

function SecurityTab() {
  const [f, setF] = useState({ current: "", next: "" });
  const m = useMutation({
    mutationFn: () => api.post("/api/users/me/password", { current_password: f.current, new_password: f.next }),
    onSuccess: () => { toast.success("Password changed. Other devices have been signed out."); setF({ current: "", next: "" }); },
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <Section title="Change password" description="Changing your password signs you out on all other devices.">
      <form className="max-w-md space-y-4" onSubmit={(e) => { e.preventDefault(); m.mutate(); }}>
        <Field id="cur" label="Current password"><PasswordInput autoComplete="current-password" value={f.current} onChange={(e) => setF({ ...f, current: e.target.value })} required /></Field>
        <Field id="new" label="New password"><PasswordInput autoComplete="new-password" value={f.next} onChange={(e) => setF({ ...f, next: e.target.value })} required /></Field>
        {f.next && <PasswordStrength password={f.next} />}
        <Button type="submit" loading={m.isPending} disabled={!passwordChecks(f.next).every((c) => c.ok)}>Update password</Button>
      </form>
    </Section>
  );
}

function PrivacyTab() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const confirm = useConfirm();
  const [open, setOpen] = useState(false);
  const [pw, setPw] = useState("");
  const m = useMutation({
    mutationFn: () => api.del("/api/users/me", { password: pw }),
    onSuccess: async () => {
      await logout();
      toast.success("Your account has been deleted.");
      navigate("/");
    },
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <div className="space-y-6">
      <Section title="Your data" description="What we hold and how it's used is explained in our Privacy Policy.">
        <ul className="space-y-2 text-sm text-slate-600">
          <li>• Your email and phone number are never displayed publicly.</li>
          <li>• Administrators access member data only as their role requires, and every action is audit-logged.</li>
          <li>• You can request a copy of your data via the <Link to="/contact" className="font-semibold text-green-600">contact form</Link>.</li>
        </ul>
        <Button asChild variant="outline" className="mt-5"><Link to="/privacy">Read the Privacy Policy</Link></Button>
      </Section>
      <section className="rounded-2xl border border-red-200 bg-red-50/40 p-5 sm:p-7">
        <h2 className="flex items-center gap-2 text-lg font-extrabold text-red-700"><ShieldAlert className="size-5" /> Delete account</h2>
        <p className="mt-1 text-sm text-slate-600">Removes your contact details and signs you out everywhere. Your posts remain but are shown as "Former member". This cannot be undone.</p>
        <Button
          variant="destructive"
          className="mt-5"
          onClick={async () => {
            if (await confirm({ title: "Delete your NIPAM account?", description: "You will need to enter your password to confirm.", confirmLabel: "Continue", destructive: true })) setOpen(true);
          }}
        >
          Delete my account
        </Button>
      </section>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm with your password</DialogTitle>
            <DialogDescription>This permanently deletes your account.</DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); m.mutate(); }}>
            <Field id="del-pw" label="Password"><PasswordInput autoComplete="current-password" value={pw} onChange={(e) => setPw(e.target.value)} required /></Field>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
              <Button type="submit" variant="destructive" loading={m.isPending}>Delete account</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function Settings() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const tab = params.get("tab") ?? "profile";
  useEffect(() => window.scrollTo({ top: 0 }), [tab]);
  if (!user) return null;
  return (
    <>
      <Seo title="Account settings" noindex />
      <PageHeader eyebrow="Account" title="Settings" description="Manage your profile, verification, communications and privacy." />
      <div className="container max-w-4xl py-8">
        <Tabs value={tab} onValueChange={(v) => setParams({ tab: v }, { replace: true })}>
          <TabsList aria-label="Settings sections">
            <TabsTrigger value="profile"><UserRound /> Profile</TabsTrigger>
            <TabsTrigger value="verification"><CheckCircle2 /> Verification</TabsTrigger>
            <TabsTrigger value="notifications"><Bell /> Notifications</TabsTrigger>
            <TabsTrigger value="security"><KeyRound /> Security</TabsTrigger>
            <TabsTrigger value="privacy"><ShieldAlert /> Privacy</TabsTrigger>
          </TabsList>
          <TabsContent value="profile"><ProfileTab user={user} /></TabsContent>
          <TabsContent value="verification">
            <Section title="Verification" description="Verified members can register for events and take part in the community.">
              <div className="space-y-3">
                <VerifyRow channel="email" user={user} />
                <VerifyRow channel="sms" user={user} />
              </div>
            </Section>
          </TabsContent>
          <TabsContent value="notifications"><NotificationsTab user={user} /></TabsContent>
          <TabsContent value="security"><SecurityTab /></TabsContent>
          <TabsContent value="privacy"><PrivacyTab /></TabsContent>
        </Tabs>
      </div>
    </>
  );
}
