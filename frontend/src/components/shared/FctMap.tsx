import { ArrowRight, Info, Users } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { Council } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Schematic (not geographic) layout of the six FCT Area Councils showing their
 * approximate relative positions. It is not a boundary map: if official GIS
 * boundaries are adopted, replace REGIONS with authoritative data and cite the
 * source in the caption.
 */
const REGIONS: Record<string, { d: string; label: [number, number] }> = {
  bwari: { d: "M150 24 L322 34 L352 128 L236 152 L164 120 Z", label: [252, 88] },
  amac: { d: "M236 152 L352 128 L382 262 L302 302 L244 252 Z", label: [310, 214] },
  gwagwalada: { d: "M82 140 L164 120 L236 152 L244 252 L152 262 L92 222 Z", label: [164, 192] },
  kuje: { d: "M152 262 L244 252 L302 302 L292 382 L194 372 Z", label: [236, 318] },
  kwali: { d: "M40 242 L92 222 L152 262 L194 372 L112 382 L52 322 Z", label: [116, 306] },
  abaji: { d: "M18 332 L52 322 L112 382 L194 372 L164 430 L38 420 Z", label: [100, 402] },
};

export function FctMap({ councils, className }: { councils: Council[]; className?: string }) {
  const [active, setActive] = useState<string>(councils[0]?.slug ?? "amac");
  const navigate = useNavigate();
  const current = councils.find((c) => c.slug === active);

  return (
    <div className={cn("grid items-center gap-8 lg:grid-cols-[1.1fr_1fr]", className)}>
      <figure className="relative">
        <svg viewBox="0 0 400 450" className="mx-auto w-full max-w-md drop-shadow-[0_18px_30px_rgba(6,59,102,0.18)]" role="group" aria-label="Schematic map of the six FCT Area Councils">
          {councils.map((c) => {
            const r = REGIONS[c.slug];
            if (!r) return null;
            const on = c.slug === active;
            return (
              <a
                key={c.slug}
                href={`/area-councils/${c.slug}`}
                aria-label={`${c.name}: open council page`}
                onMouseEnter={() => setActive(c.slug)}
                onFocus={() => setActive(c.slug)}
                onClick={(e) => {
                  e.preventDefault();
                  navigate(`/area-councils/${c.slug}`);
                }}
                className="cursor-pointer outline-none [&:focus-visible>path]:stroke-green-300"
              >
                <path
                  d={r.d}
                  className={cn("transition-all duration-300", on ? "fill-green-600" : "fill-navy-700 hover:fill-navy-600")}
                  stroke="#FFFFFF"
                  strokeWidth={on ? 4 : 3}
                  strokeLinejoin="round"
                />
                <text
                  x={r.label[0]}
                  y={r.label[1]}
                  textAnchor="middle"
                  className="pointer-events-none select-none fill-white font-display text-[15px] font-bold"
                >
                  {c.short_name}
                </text>
              </a>
            );
          })}
        </svg>
        <figcaption className="mt-3 flex items-start justify-center gap-1.5 text-center text-xs text-muted-foreground">
          <Info className="mt-px size-3.5 shrink-0" />
          Schematic view, not to scale. Not an official boundary map and not an indicator of electoral eligibility or polling location.
        </figcaption>
      </figure>

      <div className="space-y-3">
        {current && (
          <div key={current.slug} className="rounded-2xl bg-navy p-6 text-white shadow-lift animate-fade-up">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-green-300">Area Council</p>
            <h3 className="mt-1 text-2xl font-extrabold text-white">{current.name}</h3>
            <p className="mt-2 text-sm leading-relaxed text-navy-100">{current.summary}</p>
            <div className="mt-4 flex flex-wrap items-center gap-4 text-sm">
              <span className="flex items-center gap-1.5 text-navy-100">
                <Users className="size-4 text-green-300" /> {current.member_count ?? 0} member{current.member_count === 1 ? "" : "s"}
              </span>
              {current.headquarters && <span className="text-navy-100">HQ: {current.headquarters}</span>}
            </div>
            <Link to={`/area-councils/${current.slug}`} className="mt-5 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-navy transition hover:bg-green-50">
              Open {current.short_name} page <ArrowRight className="size-4" />
            </Link>
          </div>
        )}
        <div className="grid grid-cols-3 gap-2">
          {councils.map((c) => (
            <button
              key={c.slug}
              onClick={() => setActive(c.slug)}
              aria-pressed={c.slug === active}
              className={cn(
                "rounded-xl border px-3 py-2.5 text-sm font-semibold transition",
                c.slug === active ? "border-green-500 bg-green-50 text-green-700" : "border-border bg-white text-navy hover:border-navy-200",
              )}
            >
              {c.short_name}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
