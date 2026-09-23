import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, Clock, Mail, MapPin, MessageSquare } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { PageHeader } from "@/components/shared/PageHeader";
import { Seo } from "@/components/shared/Seo";
import { Button } from "@/components/ui/button";
import { Input, Select, Textarea } from "@/components/ui/input";
import { Field } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiError } from "@/lib/api";

export default function Contact() {
  const { user } = useAuth();
  const [form, setForm] = useState({ name: user?.full_name ?? "", email: user?.email ?? "", subject: "General enquiry", message: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [sent, setSent] = useState(false);
  const m = useMutation({
    mutationFn: () => api.post("/api/contact", form),
    onSuccess: () => setSent(true),
    onError: (e: Error) => {
      if (e instanceof ApiError && e.fields) setErrors(e.fields);
      toast.error(e.message);
    },
  });
  return (
    <>
      <Seo title="Contact" description="Get in touch with the NIPAM team." />
      <PageHeader eyebrow="Contact" title="Get in touch" description="Questions, corrections to a record, or ideas for the community? Send us a message." crumbs={[{ to: "/", label: "Home" }, { label: "Contact" }]} />
      <div className="container grid gap-10 py-12 lg:grid-cols-[1fr_1.4fr]">
        <aside className="space-y-4">
          {[
            [MapPin, "Location", "Federal Capital Territory, Abuja, Nigeria"],
            [Mail, "Email", "Use the form — messages go directly to the NIPAM team."],
            [Clock, "Response time", "We aim to reply within a few working days."],
          ].map(([Icon, t, d]) => {
            const I = Icon as typeof MapPin;
            return (
              <div key={t as string} className="flex gap-4 rounded-2xl border border-border p-5">
                <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-navy text-white"><I className="size-5" /></span>
                <div>
                  <p className="font-bold text-navy">{t as string}</p>
                  <p className="text-sm text-muted-foreground">{d as string}</p>
                </div>
              </div>
            );
          })}
          <div className="rounded-2xl bg-surface p-5 text-sm text-slate-600 ring-1 ring-border">
            <MessageSquare className="mb-2 size-5 text-green-600" />
            Want to discuss with other residents? Try the <Link to="/community" className="font-semibold text-green-600">community</Link>. Reporting a post? Use the Report button on the post itself.
          </div>
        </aside>
        <div className="rounded-2xl border border-border bg-white p-6 shadow-card sm:p-8">
          {sent ? (
            <div className="flex flex-col items-center py-10 text-center">
              <CheckCircle2 className="size-12 text-green-600" />
              <h2 className="mt-4 text-2xl font-extrabold">Message received</h2>
              <p className="mt-2 max-w-sm text-muted-foreground">Thank you for contacting NIPAM. A member of the team will respond by email.</p>
              <Button variant="outline" className="mt-6" onClick={() => { setSent(false); setForm((f) => ({ ...f, message: "" })); }}>Send another message</Button>
            </div>
          ) : (
            <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); setErrors({}); m.mutate(); }}>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field id="c-name" label="Your name" error={errors.name}><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required autoComplete="name" /></Field>
                <Field id="c-email" label="Email address" error={errors.email}><Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required autoComplete="email" /></Field>
              </div>
              <Field id="c-subject" label="Subject">
                <Select value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })}>
                  {["General enquiry", "Correction to a record", "Events", "Membership & account", "Privacy / data request", "Media"].map((s) => <option key={s}>{s}</option>)}
                </Select>
              </Field>
              <Field id="c-message" label="Message" error={errors.message} hint="Please don't include sensitive personal information.">
                <Textarea value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} required minLength={10} maxLength={5000} className="min-h-[160px]" />
              </Field>
              <Button type="submit" size="lg" loading={m.isPending}>Send message</Button>
              <p className="text-xs text-muted-foreground">We use your details only to reply to this message. See our <Link to="/privacy" className="font-semibold text-green-600">Privacy Policy</Link>.</p>
            </form>
          )}
        </div>
      </div>
    </>
  );
}
