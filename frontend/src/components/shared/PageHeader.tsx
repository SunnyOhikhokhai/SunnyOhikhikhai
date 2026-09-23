import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

export function PageHeader({
  eyebrow,
  title,
  description,
  crumbs,
  actions,
  className,
  children,
}: {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  crumbs?: { to?: string; label: string }[];
  actions?: ReactNode;
  className?: string;
  children?: ReactNode;
}) {
  return (
    <header className={cn("relative overflow-hidden bg-navy text-white", className)}>
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(7,148,71,0.28),transparent_55%)]" />
      <div className="pointer-events-none absolute -right-24 -top-24 size-80 rounded-full border-[28px] border-white/[0.04]" />
      <div className="container relative py-12 sm:py-16">
        {crumbs && (
          <nav aria-label="Breadcrumb" className="mb-5">
            <ol className="flex flex-wrap items-center gap-1 text-sm text-navy-200">
              {crumbs.map((c, i) => (
                <li key={i} className="flex items-center gap-1">
                  {i > 0 && <ChevronRight className="size-3.5 opacity-60" aria-hidden />}
                  {c.to ? (
                    <Link to={c.to} className="hover:text-white">
                      {c.label}
                    </Link>
                  ) : (
                    <span aria-current="page" className="text-white/90">
                      {c.label}
                    </span>
                  )}
                </li>
              ))}
            </ol>
          </nav>
        )}
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            {eyebrow && <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-green-300">{eyebrow}</p>}
            <h1 className="text-3xl font-extrabold text-white sm:text-4xl lg:text-[2.75rem] lg:leading-[1.1]">{title}</h1>
            {description && <p className="mt-4 text-base leading-relaxed text-navy-100 sm:text-lg">{description}</p>}
          </div>
          {actions && <div className="flex shrink-0 flex-wrap gap-3">{actions}</div>}
        </div>
        {children}
      </div>
    </header>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  action,
  className,
  align = "left",
}: {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
  align?: "left" | "center";
}) {
  return (
    <div className={cn("mb-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between", align === "center" && "items-center text-center sm:flex-col sm:items-center", className)}>
      <div className={cn("max-w-2xl", align === "center" && "mx-auto")}>
        {eyebrow && <p className="eyebrow mb-3">{eyebrow}</p>}
        <h2 className="text-3xl font-extrabold sm:text-4xl">{title}</h2>
        {description && <p className="mt-3 text-base leading-relaxed text-muted-foreground sm:text-lg">{description}</p>}
      </div>
      {action}
    </div>
  );
}
