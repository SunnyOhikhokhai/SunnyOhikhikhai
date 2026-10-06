import { cn } from "@/lib/utils";

export const FULL_NAME = "Non-Indigenous Movement for Philip Aduda";
export const TAGLINE = "FCT United for a Brighter Tomorrow";

/**
 * NIMPA emblem from the official logo (public/brand/nimpa-mark.png). On dark
 * backgrounds it sits on a white disc, because the artwork uses navy.
 */
export function LogoMark({ className, onDark = false, title = "NIMPA" }: { className?: string; onDark?: boolean; title?: string }) {
  const img = <img src="/brand/nimpa-mark.png" alt={title} width={512} height={512} className={onDark ? "size-[86%]" : "size-full"} />;
  return (
    <span className={cn("inline-grid size-10 shrink-0 place-items-center", onDark && "rounded-full bg-white shadow-sm", className)}>
      {img}
    </span>
  );
}

/** The complete official logo: emblem, NIMPA, full name and tagline. */
export function FullLogo({ className, onDark = false }: { className?: string; onDark?: boolean }) {
  return (
    <span className={cn("inline-block", onDark && "rounded-2xl bg-white p-4", className)}>
      <img src="/brand/nimpa-logo.png" alt={`NIMPA — ${FULL_NAME}. ${TAGLINE}.`} width={1390} height={999} className="h-auto w-full" />
    </span>
  );
}

type Variant = "full" | "with-name" | "compact";

export function Logo({
  variant = "full",
  tone = "light",
  className,
}: {
  variant?: Variant;
  /** light = for white backgrounds; dark = for navy/green backgrounds */
  tone?: "light" | "dark";
  className?: string;
}) {
  const dark = tone === "dark";
  if (variant === "compact") return <LogoMark className={className} onDark={dark} />;
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark onDark={dark} className={variant === "with-name" ? "size-12" : "size-10"} title="" />
      <span className="flex flex-col leading-none">
        <span className={cn("font-display text-[1.45rem] font-extrabold tracking-[0.08em]", dark ? "text-white" : "text-navy")}>
          NIMP<span className={dark ? "text-green-300" : "text-green-500"}>A</span>
        </span>
        {variant === "with-name" && (
          <span className={cn("mt-1 max-w-[14rem] text-[10px] font-semibold uppercase leading-tight tracking-[0.12em]", dark ? "text-navy-100" : "text-silver-dark")}>
            {FULL_NAME}
          </span>
        )}
      </span>
    </span>
  );
}
