import { ArrowRight, BadgeCheck, CalendarCheck, Eye, HeartHandshake, Lock, MessageSquare, Scale, UserPlus } from "lucide-react";
import { Link } from "react-router-dom";
import { PageHeader, SectionHeading } from "@/components/shared/PageHeader";
import { Seo } from "@/components/shared/Seo";
import { Button } from "@/components/ui/button";
import { PILLARS } from "./Home";

const VALUES = [
  { icon: HeartHandshake, title: "Inclusion", text: "Everyone living in the FCT is welcome, whatever their state of origin, background or faith." },
  { icon: Scale, title: "Accuracy", text: "We distinguish verified facts from announcements, opinion and user contributions." },
  { icon: Eye, title: "Transparency", text: "Records carry their sources and status. Corrections are welcome." },
  { icon: Lock, title: "Privacy", text: "Member contact details are never published. You control your communications." },
];

const STEPS = [
  { icon: UserPlus, title: "Join", text: "Create a free account and choose the Area Council you live in." },
  { icon: CalendarCheck, title: "Attend", text: "Register for town halls, forums and community activities." },
  { icon: MessageSquare, title: "Discuss", text: "Share ideas and questions in moderated community discussions." },
  { icon: BadgeCheck, title: "Inform", text: "Follow Our Record and flag information that needs correction." },
];

export default function About() {
  return (
    <>
      <Seo title="About" description="What NIPAM is, why it exists, its values and how people can take part." />
      <PageHeader
        eyebrow="About NIPAM"
        title="Non-Indigenes for Philip Aduda Movement"
        description="NIPAM is a voluntary community of residents and members across the Federal Capital Territory, focused on accessible information and constructive civic participation."
        crumbs={[{ to: "/", label: "Home" }, { label: "About" }]}
      />

      <section className="section">
        <div className="container grid gap-12 lg:grid-cols-2">
          <div>
            <p className="eyebrow mb-3">What NIPAM is</p>
            <h2 className="text-3xl font-extrabold">A civic community for FCT residents</h2>
            <div className="prose-nipam mt-5">
              <p>
                The Federal Capital Territory is home to people from every part of Nigeria. NIPAM exists to connect residents — including those
                who are not indigenes of the Territory — around shared community life, reliable information and constructive participation.
              </p>
              <p>
                This platform is NIPAM's digital home. It brings together news and announcements, events, Area Council information, a
                documented public record library and a moderated community space.
              </p>
            </div>
          </div>
          <div>
            <p className="eyebrow mb-3">Why it exists</p>
            <h2 className="text-3xl font-extrabold">Information people can trust</h2>
            <div className="prose-nipam mt-5">
              <p>
                Residents deserve clear, accessible information about their communities. NIPAM documents public records with their sources and
                labels each item so that verified information, announcements, opinion and user-generated content are never confused.
              </p>
              <p>
                Membership is voluntary. NIPAM does not infer anyone's views from ethnicity, religion, indigene status or other personal
                characteristics, and members choose which messages they receive.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="section bg-surface">
        <div className="container">
          <SectionHeading eyebrow="Our pillars" title="Community · Information · Participation" align="center" />
          <div className="grid gap-6 md:grid-cols-3">
            {PILLARS.map(({ icon: Icon, title, text }) => (
              <div key={title} className="rounded-2xl border border-border bg-white p-7 shadow-card">
                <div className="flex size-14 items-center justify-center rounded-2xl bg-navy text-white">
                  <Icon className="size-7" />
                </div>
                <h3 className="mt-5 text-xl font-extrabold uppercase tracking-[0.08em]">{title}</h3>
                <p className="mt-2 leading-relaxed text-muted-foreground">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <SectionHeading eyebrow="Our values" title="How we work" />
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {VALUES.map(({ icon: Icon, title, text }) => (
              <div key={title} className="rounded-2xl border border-border p-6">
                <Icon className="size-7 text-green-600" />
                <h3 className="mt-4 text-lg font-bold">{title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section bg-navy text-white">
        <div className="container">
          <SectionHeading eyebrow="Participate" title={<span className="text-white">How you can take part</span>} />
          <ol className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map(({ icon: Icon, title, text }, i) => (
              <li key={title} className="relative rounded-2xl bg-white/5 p-6 ring-1 ring-white/10">
                <span className="absolute right-5 top-4 font-display text-4xl font-extrabold text-white/10">{i + 1}</span>
                <Icon className="size-7 text-green-400" />
                <h3 className="mt-4 text-lg font-bold text-white">{title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-navy-100">{text}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="section">
        <div className="container grid gap-10 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="eyebrow mb-3">How information is managed</p>
            <h2 className="text-3xl font-extrabold">Clear labels, cited sources, accountable editing</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Content is published by authorised administrators with defined roles, and every administrative action is recorded in an audit log.
            </p>
          </div>
          <ul className="space-y-3">
            {[
              ["Verified information", "Checked against a cited source before publication."],
              ["Announcements", "Official notices from NIPAM, marked as such."],
              ["Historical records", "Documented past activities with their original references."],
              ["Opinion", "Commentary, clearly separated from factual reporting."],
              ["User-generated content", "Community posts — members' own views, moderated against our guidelines."],
            ].map(([t, d]) => (
              <li key={t} className="flex gap-3 rounded-xl border border-border p-4">
                <BadgeCheck className="mt-0.5 size-5 shrink-0 text-green-600" />
                <span>
                  <span className="font-semibold text-navy">{t}</span>
                  <span className="block text-sm text-muted-foreground">{d}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div className="container mt-14 flex flex-col items-center gap-3 text-center">
          <Button asChild size="lg">
            <Link to="/join">
              Join NIPAM <ArrowRight />
            </Link>
          </Button>
          <Link to="/privacy" className="text-sm font-semibold text-green-600 hover:underline">
            Read how we handle your data
          </Link>
        </div>
      </section>
    </>
  );
}
