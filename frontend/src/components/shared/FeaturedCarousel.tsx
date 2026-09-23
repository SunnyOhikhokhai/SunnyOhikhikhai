import { ArrowRight, CalendarDays, ChevronLeft, ChevronRight, MapPin, Pause, Play } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { CoverArt } from "@/components/brand/Artwork";
import { Button } from "@/components/ui/button";
import type { RecordCard } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";
import { DemoBadge, VerificationBadge } from "./badges";

const INTERVAL = 6500;

export function FeaturedCarousel({ items }: { items: RecordCard[] }) {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [userPaused, setUserPaused] = useState(false);
  const reduced = useRef(typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const touch = useRef<number | null>(null);
  const n = items.length;

  const go = useCallback((i: number) => setIndex(((i % n) + n) % n), [n]);

  useEffect(() => {
    if (n < 2 || paused || userPaused || reduced.current) return;
    const t = setTimeout(() => go(index + 1), INTERVAL);
    return () => clearTimeout(t);
  }, [index, paused, userPaused, n, go]);

  if (!n) return null;
  const autoplay = !userPaused && !reduced.current;

  return (
    <section
      aria-roledescription="carousel"
      aria-label="Featured records and activities"
      className="relative"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
      onKeyDown={(e) => {
        if (e.key === "ArrowRight") go(index + 1);
        if (e.key === "ArrowLeft") go(index - 1);
      }}
      onTouchStart={(e) => (touch.current = e.touches[0].clientX)}
      onTouchEnd={(e) => {
        if (touch.current === null) return;
        const dx = e.changedTouches[0].clientX - touch.current;
        if (Math.abs(dx) > 50) go(index + (dx < 0 ? 1 : -1));
        touch.current = null;
      }}
    >
      <div className="relative overflow-hidden rounded-3xl border border-border bg-white shadow-lift">
        <div className="grid min-h-[30rem] lg:min-h-[26rem]" aria-live={autoplay ? "off" : "polite"}>
          {items.map((r, i) => {
            const active = i === index;
            return (
              <article
                key={r.id}
                role="group"
                aria-roledescription="slide"
                aria-label={`${i + 1} of ${n}`}
                aria-hidden={!active}
                className={cn(
                  "col-start-1 row-start-1 grid transition-all duration-700 ease-out lg:grid-cols-[1.1fr_1fr]",
                  active ? "visible translate-x-0 opacity-100" : "invisible translate-x-4 opacity-0",
                )}
              >
                <div className="relative aspect-[16/9] overflow-hidden lg:aspect-auto">
                  {r.image ? (
                    <img src={r.image.url} alt={r.image.alt} className="size-full object-cover" loading={i === 0 ? "eager" : "lazy"} />
                  ) : (
                    <CoverArt seed={r.slug} icon={r.category.slug} className="size-full" />
                  )}
                  <span className="absolute left-4 top-4 rounded-full bg-white/95 px-3 py-1 text-xs font-bold uppercase tracking-wider text-navy shadow">
                    {r.category.name}
                  </span>
                </div>
                <div className="flex flex-col justify-center gap-4 p-6 sm:p-8 lg:p-10">
                  <div className="flex flex-wrap gap-2">
                    <VerificationBadge status={r.verification_status} />
                    {r.is_demo && <DemoBadge />}
                  </div>
                  <h3 className="text-2xl font-extrabold leading-tight sm:text-[1.75rem]">{r.title}</h3>
                  <dl className="flex flex-wrap gap-x-5 gap-y-1.5 text-sm text-slate-600">
                    <div className="flex items-center gap-1.5">
                      <dt className="sr-only">Location</dt>
                      <MapPin className="size-4 text-green-600" />
                      <dd>{r.location ?? r.area_council?.name ?? "FCT"}</dd>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <dt className="sr-only">Date</dt>
                      <CalendarDays className="size-4 text-green-600" />
                      <dd>{r.year ?? (r.record_date ? formatDate(r.record_date) : "Date to be added")}</dd>
                    </div>
                  </dl>
                  <p className="line-clamp-3 text-[15px] leading-relaxed text-muted-foreground">{r.summary}</p>
                  <div>
                    <Button asChild tabIndex={active ? 0 : -1}>
                      <Link to={`/our-record/${r.slug}`}>
                        View details <ArrowRight />
                      </Link>
                    </Button>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2" role="tablist" aria-label="Choose slide">
          {items.map((r, i) => (
            <button
              key={r.id}
              role="tab"
              aria-selected={i === index}
              aria-label={`Show slide ${i + 1}: ${r.title}`}
              onClick={() => go(i)}
              className={cn("h-2.5 rounded-full transition-all duration-300", i === index ? "w-8 bg-green-500" : "w-2.5 bg-silver-light hover:bg-silver")}
            />
          ))}
        </div>
        <div className="flex items-center gap-2">
          {!reduced.current && (
            <Button variant="ghost" size="icon" onClick={() => setUserPaused((p) => !p)} aria-label={userPaused ? "Resume rotation" : "Pause rotation"}>
              {userPaused ? <Play /> : <Pause />}
            </Button>
          )}
          <Button variant="outline" size="icon" onClick={() => go(index - 1)} aria-label="Previous slide">
            <ChevronLeft />
          </Button>
          <Button variant="outline" size="icon" onClick={() => go(index + 1)} aria-label="Next slide">
            <ChevronRight />
          </Button>
        </div>
      </div>
    </section>
  );
}
