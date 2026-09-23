import type { ContentLabel, VerificationStatus } from "./types";

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
    description: "Checked against at least one cited source by NIPAM administrators.",
  },
  pending_review: {
    label: "Pending review",
    tone: "bg-navy-50 text-navy-700 ring-navy-600/20",
    description: "Sources have been submitted and are being reviewed.",
  },
  unverified: {
    label: "Unverified",
    tone: "bg-amber-50 text-amber-800 ring-amber-600/25",
    description: "Not yet verified. Treat as unconfirmed until sources are added.",
  },
  disputed: {
    label: "Disputed",
    tone: "bg-red-50 text-red-700 ring-red-600/25",
    description: "Information in this record has been questioned and is under review.",
  },
};

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
