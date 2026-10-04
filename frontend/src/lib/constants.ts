import type { ContentLabel, LegislativeStage, ProjectStatus, VerificationStatus } from "./types";

export const NAV_LINKS = [
  { to: "/", label: "Home" },
  { to: "/philip-aduda", label: "Sen. Aduda" },
  { to: "/about", label: "About" },
  { to: "/our-record", label: "Our Record" },
  { to: "/area-councils", label: "Area Councils" },
  { to: "/news", label: "News" },
  { to: "/events", label: "Events" },
  { to: "/community", label: "Community" },
  { to: "/contact", label: "Contact" },
];

export const COUNCIL_SLUGS = ["amac", "bwari", "gwagwalada", "kuje", "kwali", "abaji"] as const;

export const VERIFICATION: Record<VerificationStatus, { label: string; tone: string; description: string }> = {
  verified: {
    label: "Verified",
    tone: "bg-green-50 text-green-700 ring-green-600/25",
    description: "Supported directly by an official government, INEC or National Assembly record.",
  },
  reported: {
    label: "Reported",
    tone: "bg-sky-50 text-sky-800 ring-sky-600/25",
    description: "Supported by credible news reporting, but not yet matched to an official primary document.",
  },
  self_reported: {
    label: "Self-reported",
    tone: "bg-violet-50 text-violet-800 ring-violet-600/25",
    description: "Published by Senator Aduda, his official website or his party. Not independently verified.",
  },
  pending: {
    label: "Pending verification",
    tone: "bg-amber-50 text-amber-800 ring-amber-600/25",
    description: "Insufficient evidence so far. Not to be read as a factual claim.",
  },
  disputed: {
    label: "Disputed",
    tone: "bg-red-50 text-red-700 ring-red-600/25",
    description: "Information in this record has been questioned and is under review.",
  },
};

export const PROJECT_STATUS: Record<ProjectStatus, { label: string; tone: string }> = {
  ongoing: { label: "Ongoing (as reported)", tone: "bg-amber-50 text-amber-800 ring-amber-600/25" },
  nearing_completion: { label: "Nearing completion (as reported)", tone: "bg-lime-50 text-lime-800 ring-lime-600/25" },
  commissioned: { label: "Commissioned (as reported)", tone: "bg-green-50 text-green-700 ring-green-600/25" },
  completed: { label: "Completed", tone: "bg-green-50 text-green-700 ring-green-600/25" },
  reported: { label: "Status not confirmed", tone: "bg-slate-100 text-slate-700 ring-slate-500/20" },
  pending: { label: "Status pending verification", tone: "bg-slate-100 text-slate-700 ring-slate-500/20" },
};

/** Legislative stages, in order. Never collapsed into a single "Passed". */
export const LEGISLATIVE_STAGES: Record<LegislativeStage, { label: string; tone: string; description: string }> = {
  proposed: { label: "Proposed", tone: "bg-slate-100 text-slate-700 ring-slate-500/20", description: "A proposal; not yet introduced as a bill." },
  introduced: { label: "Introduced", tone: "bg-sky-50 text-sky-800 ring-sky-600/25", description: "Introduced (first reading)." },
  second_reading: { label: "Second reading", tone: "bg-sky-50 text-sky-800 ring-sky-600/25", description: "Passed second reading." },
  committee_stage: { label: "Committee stage", tone: "bg-indigo-50 text-indigo-800 ring-indigo-600/25", description: "Referred to a committee for report." },
  passed_chamber: { label: "Passed by chamber", tone: "bg-green-50 text-green-700 ring-green-600/25", description: "Passed by the Senate or House. Not yet law." },
  assented: { label: "Assented / enacted", tone: "bg-green-100 text-green-800 ring-green-700/30", description: "Signed into law, per an official record." },
  self_reported_passed: {
    label: "Self-reported as passed",
    tone: "bg-violet-50 text-violet-800 ring-violet-600/25",
    description: "Described as passed by his official website; not matched to an official enactment/assent record.",
  },
  pending: { label: "Status pending verification", tone: "bg-amber-50 text-amber-800 ring-amber-600/25", description: "The legislative stage has not been confirmed." },
};

export const SOURCE_TYPES: Record<string, string> = {
  inec: "INEC",
  national_assembly: "National Assembly",
  fcta: "FCTA",
  official_site: "Senator Aduda's official website",
  party: "Party (APC)",
  news_agency: "News agency",
  news: "News publication",
  legal: "Law / Constitution",
  other: "Other",
};

export const RELIABILITY: Record<string, string> = {
  official: "Official record",
  party: "Party publication",
  self: "Self-published",
  news: "Credible news",
  other: "Other / unclassified",
};

export const PENDING_INFO = "Information pending verification.";

export const CONTENT_LABELS: Record<ContentLabel, { label: string; tone: string }> = {
  verified_information: { label: "Verified information", tone: "bg-green-50 text-green-700 ring-green-600/25" },
  announcement: { label: "Announcement", tone: "bg-navy-50 text-navy-700 ring-navy-600/20" },
  opinion: { label: "Opinion", tone: "bg-purple-50 text-purple-700 ring-purple-600/20" },
  historical_record: { label: "Historical record", tone: "bg-slate-100 text-slate-700 ring-slate-500/20" },
  update: { label: "Update", tone: "bg-sky-50 text-sky-800 ring-sky-600/20" },
};

export const REPORT_REASONS = [
  ["hate_speech", "Hate speech"],
  ["threat", "Threats or incitement"],
  ["harassment", "Harassment or bullying"],
  ["impersonation", "Impersonation"],
  ["false_claim", "False claim presented as fact"],
  ["doxxing", "Doxxing"],
  ["personal_information", "Exposes personal information"],
  ["spam", "Spam"],
  ["other", "Something else"],
] as const;

export const SITE_URL = typeof window !== "undefined" ? window.location.origin : "";
