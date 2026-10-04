import { ExternalLink } from "lucide-react";
import { NavLink } from "react-router-dom";
import type { VerificationStatus } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";
import { VerificationBadge } from "./badges";

const isHttp = (u?: string | null) => !!u && /^https?:\/\//.test(u);

/** The three facts every public record shows: Source, Verification, Last updated. */
export function SourceLine({
  source,
  sourceUrl,
  verification,
  updated,
  className,
}: {
  source?: string | null;
  sourceUrl?: string | null;
  verification?: VerificationStatus | null;
  updated?: string | null;
  className?: string;
}) {
  return (
    <dl className={cn("grid gap-x-6 gap-y-1.5 text-sm sm:grid-cols-[auto_1fr]", className)}>
      <dt className="font-semibold text-navy">Source</dt>
      <dd className="min-w-0 text-slate-600">
        {source ? (
          isHttp(sourceUrl) ? (
            <a href={sourceUrl!} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 break-words font-medium text-green-700 hover:underline">
              {source} <ExternalLink className="size-3.5 shrink-0" aria-hidden />
            </a>
          ) : (
            source
          )
        ) : (
          "Information pending verification."
        )}
      </dd>
      {verification && (
        <>
          <dt className="font-semibold text-navy">Verification</dt>
          <dd>
            <VerificationBadge status={verification} />
          </dd>
        </>
      )}
      {updated && (
        <>
          <dt className="font-semibold text-navy">Last updated</dt>
          <dd className="text-slate-600">{formatDate(updated, { day: "numeric", month: "long", year: "numeric" })}</dd>
        </>
      )}
    </dl>
  );
}

export interface CitedSource {
  name: string;
  title?: string | null;
  url: string | null;
  note?: string | null;
  publication_date?: string | null;
}

/** Numbered list of every source an item cites. */
export function SourceList({ sources, className }: { sources: CitedSource[]; className?: string }) {
  if (!sources.length) return <p className={cn("text-sm text-muted-foreground", className)}>Information pending verification.</p>;
  return (
    <ol className={cn("space-y-3", className)}>
      {sources.map((s, i) => (
        <li key={`${s.url ?? s.name}-${i}`} className="flex gap-3 text-sm">
          <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-navy-50 text-xs font-bold text-navy">{i + 1}</span>
          <div className="min-w-0">
            <p className="font-semibold text-navy">{s.name}</p>
            {s.title && <p className="text-slate-600">{s.title}</p>}
            {s.note && <p className="text-[13px] text-muted-foreground">{s.note}</p>}
            {s.publication_date && <p className="text-[13px] text-muted-foreground">Published {formatDate(s.publication_date)}</p>}
            {isHttp(s.url) && (
              <a href={s.url!} target="_blank" rel="noopener noreferrer" className="inline-flex max-w-full items-center gap-1 break-all text-[13px] font-medium text-green-700 hover:underline">
                {s.url!.replace(/^https?:\/\/(www\.)?/, "").slice(0, 80)}
                <ExternalLink className="size-3 shrink-0" aria-hidden />
              </a>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}

/** Switch between the three parts of the public record. */
export function RecordTabs() {
  const tabs = [
    { to: "/our-record", label: "Constituency projects" },
    { to: "/legislation", label: "Legislation" },
    { to: "/elections", label: "Elections" },
  ];
  return (
    <nav aria-label="Public record" className="mt-6 flex gap-1 overflow-x-auto rounded-2xl bg-white/10 p-1 text-sm font-semibold sm:inline-flex">
      {tabs.map((t) => (
        <NavLink
          key={t.to}
          to={t.to}
          end
          className={({ isActive }) =>
            cn("whitespace-nowrap rounded-xl px-3.5 py-2 transition", isActive ? "bg-white text-navy" : "text-white/85 hover:bg-white/10 hover:text-white")
          }
        >
          {t.label}
        </NavLink>
      ))}
    </nav>
  );
}
