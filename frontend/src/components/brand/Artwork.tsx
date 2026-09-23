import {
  Briefcase,
  Building2,
  CalendarDays,
  FileText,
  GraduationCap,
  Handshake,
  HeartPulse,
  Landmark,
  Newspaper,
  Route,
  Sparkles,
  Trophy,
  Users,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const CATEGORY_ICONS: Record<string, LucideIcon> = {
  infrastructure: Building2,
  education: GraduationCap,
  healthcare: HeartPulse,
  roads: Route,
  "community-development": Users,
  youth: Sparkles,
  sports: Trophy,
  "employment-economic-development": Briefcase,
  "legislative-activity": Landmark,
  "constituency-engagement": Handshake,
  other: FileText,
  news: Newspaper,
  event: CalendarDays,
};

function hash(s: string) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

/** Branded generated cover used when content has no photograph. */
export function CoverArt({
  seed,
  icon = "other",
  label,
  className,
}: {
  seed: string;
  icon?: string;
  label?: string;
  className?: string;
}) {
  const Icon = CATEGORY_ICONS[icon] ?? FileText;
  const h = hash(seed);
  const variant = h % 3;
  const bg = ["from-navy-700 to-navy-900", "from-navy-600 to-navy-800", "from-navy-800 to-green-800"][variant];
  const rot = (h % 40) - 20;
  return (
    <div className={cn("relative isolate overflow-hidden bg-gradient-to-br", bg, className)} aria-hidden>
      <svg className="absolute inset-0 size-full opacity-[0.14]" preserveAspectRatio="xMidYMid slice" viewBox="0 0 400 250">
        <defs>
          <pattern id={`p${h}`} width="28" height="28" patternUnits="userSpaceOnUse" patternTransform={`rotate(${rot})`}>
            <circle cx="3" cy="3" r="1.6" fill="#fff" />
          </pattern>
        </defs>
        <rect width="400" height="250" fill={`url(#p${h})`} />
      </svg>
      <svg className="absolute -right-10 -top-16 size-64 text-green-500/25" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="46" fill="none" stroke="currentColor" strokeWidth="10" />
      </svg>
      <div className="absolute bottom-0 left-0 h-1.5 w-full bg-gradient-to-r from-green-500 via-green-400 to-transparent" />
      <div className="relative flex h-full items-center justify-center">
        <div className="flex size-16 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/20 backdrop-blur-sm sm:size-20">
          <Icon className="size-8 text-white sm:size-10" strokeWidth={1.6} />
        </div>
      </div>
      {label && (
        <span className="absolute bottom-4 left-4 text-[11px] font-semibold uppercase tracking-[0.14em] text-white/70">{label}</span>
      )}
    </div>
  );
}

/** Abstract Abuja/FCT skyline: Aso Rock profile, city gate arch and skyline. */
export function SkylineArt({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 1440 360" preserveAspectRatio="xMidYMax slice" aria-hidden>
      <defs>
        <linearGradient id="rock" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0C4A7D" />
          <stop offset="1" stopColor="#052F52" />
        </linearGradient>
        <linearGradient id="city" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#063B66" />
          <stop offset="1" stopColor="#04243F" />
        </linearGradient>
      </defs>
      {/* Aso Rock inspired monolith */}
      <path
        d="M860 360 C 880 250 930 150 1010 112 C 1060 88 1120 92 1170 120 C 1240 160 1290 230 1320 300 L 1350 360 Z"
        fill="url(#rock)"
        opacity=".85"
      />
      <path d="M0 360 C 180 300 320 290 470 318 C 600 340 700 320 860 300 L 860 360 Z" fill="#0C4A7D" opacity=".5" />
      {/* Skyline */}
      <g fill="url(#city)">
        <rect x="120" y="230" width="46" height="130" rx="3" />
        <rect x="176" y="200" width="38" height="160" rx="3" />
        <rect x="224" y="250" width="54" height="110" rx="3" />
        <rect x="560" y="210" width="40" height="150" rx="3" />
        <rect x="608" y="180" width="30" height="180" rx="3" />
        <rect x="646" y="236" width="56" height="124" rx="3" />
        <path d="M720 360 V 262 a 44 44 0 0 1 88 0 V 360 Z" />
        <rect x="760" y="206" width="8" height="30" />
        <rect x="1180" y="240" width="44" height="120" rx="3" />
        <rect x="1232" y="214" width="34" height="146" rx="3" />
      </g>
      {/* City gate arch */}
      <g fill="none" stroke="#079447" strokeWidth="10" strokeLinecap="round" opacity=".9">
        <path d="M330 360 V 262 Q 330 214 380 214 H 430 Q 480 214 480 262 V 360" />
      </g>
      <g fill="#9BDFB8" opacity=".35">
        {Array.from({ length: 18 }).map((_, i) => (
          <rect key={i} x={126 + (i % 3) * 14 + (i > 8 ? 440 : 0)} y={244 + Math.floor((i % 9) / 3) * 26} width="6" height="10" rx="1" />
        ))}
      </g>
      <rect y="352" width="1440" height="8" fill="#079447" />
    </svg>
  );
}
